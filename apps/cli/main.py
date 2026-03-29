from __future__ import annotations

import asyncio
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Optional

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

import typer
from rich.prompt import Prompt

from apps.cli.ui import console, display_banner, display_config, display_result, display_status
from packages.agents import CodexAdapter, GeminiAdapter
from packages.agents.base import AgentAdapter, AgentSelection, AgentTurnRequest
from packages.agents.claude_adapter import ClaudeAdapter
from packages.agents.drivers.claude_cli import ClaudeCLIQuotaError
from packages.config import ConfigLoader, ConfigService
from packages.domain.models.project import Project
from packages.orchestrator.hive import HiveOrchestrator

app = typer.Typer(help="OrchAI: CLI-First AI Orchestrator")

# Maps completed role → label for the NEXT waiting phase
_NEXT_PHASE_LABEL = {
    "planner": "Worker is implementing",
    "worker": "Refiner is reviewing",
    "refiner": "Worker is implementing",
    "architect": "Worker resuming with feedback",
}
_REPL_HISTORY_WINDOW = 6
_PROVIDER_MENU = {
    "1": {"provider": "claude", "mode": "cli", "label": "Claude CLI", "status": "ready"},
    "2": {"provider": "claude", "mode": "api", "label": "Claude API", "status": "ready"},
    "3": {"provider": "gemini", "mode": None, "label": "Gemini", "status": "stub"},
    "4": {"provider": "codex", "mode": None, "label": "Codex", "status": "stub"},
}


# ── Commands ──────────────────────────────────────────────────────────────────

@app.callback(invoke_without_command=True)
def entrypoint(
    ctx: typer.Context,
    provider: Optional[str] = typer.Option(None, help="Provider override: claude, gemini, codex"),
    model: Optional[str] = typer.Option(None, help="Model override"),
    mode: Optional[str] = typer.Option(None, help="Driver mode: cli or api"),
):
    """Start the interactive OrchAI shell when no subcommand is provided."""
    if ctx.invoked_subcommand is not None:
        return

    try:
        asyncio.run(_run_repl(provider, model, mode))
    except ClaudeCLIQuotaError as exc:
        _exit_for_claude_quota(exc)


@app.command()
def chat(
    prompt: str = typer.Argument(..., help="The prompt for the AI"),
    provider: Optional[str] = typer.Option(None, help="Provider override: claude, gemini, codex"),
    model: Optional[str] = typer.Option(None, help="Model override"),
    mode: Optional[str] = typer.Option(None, help="Driver mode: cli or api"),
):
    """Single-turn conversation with the AI worker."""
    try:
        asyncio.run(_run_single_turn(prompt, provider, model, mode, show_banner=True))
    except ClaudeCLIQuotaError as exc:
        _exit_for_claude_quota(exc)


@app.command()
def repl(
    provider: Optional[str] = typer.Option(None, help="Provider override: claude, gemini, codex"),
    model: Optional[str] = typer.Option(None, help="Model override"),
    mode: Optional[str] = typer.Option(None, help="Driver mode: cli or api"),
):
    """Interactive REPL that keeps the conversation open."""
    try:
        asyncio.run(_run_repl(provider, model, mode))
    except ClaudeCLIQuotaError as exc:
        _exit_for_claude_quota(exc)


@app.command()
def orchestrate(
    prompt: str = typer.Argument(..., help="Complex task for the AI team"),
    provider: Optional[str] = typer.Option(None, help="Provider override: claude, gemini, codex"),
    model: Optional[str] = typer.Option(None, help="Model override"),
    mode: Optional[str] = typer.Option(None, help="Driver mode: cli or api"),
    max_turns: int = typer.Option(5, help="Maximum Planner→Worker→Refiner cycles"),
):
    """Full autonomous Planner → Worker → Refiner orchestration loop."""
    try:
        asyncio.run(_run_full_orchestration(prompt, provider, model, mode, max_turns))
    except ClaudeCLIQuotaError as exc:
        _exit_for_claude_quota(exc)


# ── Async runners ─────────────────────────────────────────────────────────────

async def _run_single_turn(
    prompt: str,
    provider: Optional[str],
    model: Optional[str],
    mode: Optional[str],
    *,
    show_banner: bool = True,
) -> None:
    if show_banner:
        display_banner()

    adapter, selection = _build_worker_runtime(provider, model, mode)
    result = await _run_worker_turn(adapter, selection, prompt, project_id="cli-single-turn")
    _display_worker_result(result.output)


async def _run_repl(provider: Optional[str], model: Optional[str], mode: Optional[str]) -> None:
    display_banner()

    adapter, selection = _build_worker_runtime(provider, model, mode)
    history: list[tuple[str, str]] = []

    console.print(
        "[bold magenta]Interactive mode[/bold magenta] "
        "[dim](enter /exit to quit, /clear to reset the conversation)[/dim]\n"
    )

    while True:
        user_prompt = Prompt.ask("[bold cyan]You[/bold cyan]").strip()
        if not user_prompt:
            continue
        if user_prompt.lower() in {"/exit", "/quit"}:
            console.print("\n[dim]Session closed.[/dim]\n")
            return
        if user_prompt.lower() == "/clear":
            history.clear()
            console.print("[dim]Conversation cleared.[/dim]\n")
            continue

        prompt = _build_repl_prompt(user_prompt, history)
        result = await _run_worker_turn(adapter, selection, prompt, project_id="cli-repl")
        _display_worker_result(result.output)
        history.append((user_prompt, result.output))


def _build_worker_runtime(
    provider: Optional[str],
    model: Optional[str],
    mode: Optional[str],
) -> tuple[AgentAdapter, AgentSelection]:
    root_path = Path(".")
    config_service = ConfigService(ConfigLoader(root_path).load())
    chosen_provider, chosen_mode = _resolve_provider_choice(provider, mode)

    if chosen_provider == "claude":
        params = {"driver_mode": chosen_mode} if chosen_mode else {}
        resolved = config_service.resolve_claude_config(parameters=params, model=model)
        display_config({
            "provider": "claude",
            "model": resolved.model,
            "driver_mode": resolved.mode,
            "cli_command": resolved.cli_command,
            "timeout": resolved.timeout,
            "status": "ready",
        })
        adapter = ClaudeAdapter(config_service=config_service)
        selection = AgentSelection(role="worker", provider="claude", model=model, parameters=params)
        return adapter, selection

    display_config({
        "provider": chosen_provider,
        "model": model,
        "driver_mode": "n/a",
        "status": "stub",
    })
    console.print(
        f"[yellow]{chosen_provider} adapter is currently a stub in this repo. "
        f"It will return placeholder responses until a real driver is implemented.[/yellow]"
    )
    adapter = GeminiAdapter() if chosen_provider == "gemini" else CodexAdapter()
    selection = AgentSelection(role="worker", provider=chosen_provider, model=model, parameters={})
    return adapter, selection


async def _run_worker_turn(
    adapter: ClaudeAdapter,
    selection: AgentSelection,
    prompt: str,
    *,
    project_id: str,
):
    project = Project(
        project_id=project_id,
        repo_url="https://github.com/OrchAI",
        workspace_path=".",
        chat_platform="cli",
    )
    request = AgentTurnRequest(
        project=project,
        role="worker",
        prompt=prompt,
        agent_selection=selection,
    )

    display_status("OrchAI", f"Sending prompt to Claude")
    with _spinner("Waiting for Claude response..."):
        return await adapter.run_turn(request)


def _display_worker_result(output: str) -> None:
    display_result("worker", output)


async def _run_full_orchestration(
    prompt: str,
    provider: Optional[str],
    model: Optional[str],
    mode: Optional[str],
    max_turns: int,
) -> None:
    display_banner()

    project = Project(
        project_id="hive-orchestration",
        repo_url="https://github.com/OrchAI",
        workspace_path=".",
        chat_platform="cli",
    )

    adapter, _ = _build_worker_runtime(provider, model, mode)
    orchestrator = HiveOrchestrator(adapter=adapter, max_turns=max_turns)

    console.print(
        f"\n[bold magenta]▶ HiveMind[/bold magenta] [dim]Planner → Worker → Refiner[/dim]"
        f"\n[dim]Task:[/dim] [italic white]{prompt}[/italic white]\n"
    )

    turn_count = 0
    with console.status("[bold cyan]Planner is analyzing...[/bold cyan]", spinner="dots") as status:
        async for turn in orchestrator.execute_stream(prompt, project):
            # Stop spinner cleanly so display_result prints without interference
            status.stop()

            turn_count += 1
            _render_turn_header(turn_count, turn.role)
            display_result(turn.role, turn.output)

            # If loop continues, show what's coming next
            next_label = _NEXT_PHASE_LABEL.get(turn.role)
            if next_label and not turn.output.strip().upper().startswith("DONE"):
                status.update(f"[bold cyan]{next_label}...[/bold cyan]")
                status.start()

    console.print(
        f"\n[bold green]✓ Orchestration complete[/bold green] "
        f"[dim]({turn_count} turns)[/dim]\n"
    )


# ── Helpers ───────────────────────────────────────────────────────────────────

def _render_turn_header(turn_count: int, role: str) -> None:
    role_colors = {
        "planner": "bright_blue",
        "worker": "bright_yellow",
        "refiner": "bright_green",
        "architect": "bright_red",
    }
    color = role_colors.get(role, "white")
    console.print(
        f"[bold {color}]── Turn {turn_count}: {role.upper()} "
        f"──────────────────────────────[/bold {color}]"
    )


def _exit_for_claude_quota(exc: ClaudeCLIQuotaError) -> None:
    console.print("\n[bold red]Claude CLI usage limit reached.[/bold red]")
    if exc.reset_at:
        console.print(f"[yellow]Reset:[/yellow] {exc.reset_at}")
    console.print("[dim]Retry later, switch to `--mode api`, or update your Claude CLI account limits.[/dim]\n")
    raise typer.Exit(code=1)


def _resolve_provider_choice(
    provider: Optional[str],
    mode: Optional[str],
) -> tuple[str, Optional[str]]:
    normalized_provider = provider.lower() if provider else None
    normalized_mode = mode.lower() if mode else None

    if normalized_provider is not None:
        if normalized_provider not in {"claude", "gemini", "codex"}:
            raise typer.BadParameter("Provider must be one of: claude, gemini, codex")
        if normalized_provider != "claude" and normalized_mode is not None:
            console.print("[yellow]Ignoring --mode because it only applies to the Claude provider.[/yellow]")
            normalized_mode = None
        return normalized_provider, normalized_mode

    return _prompt_for_provider_choice()


def _prompt_for_provider_choice() -> tuple[str, Optional[str]]:
    console.print("[bold magenta]Select AI provider[/bold magenta]")
    for option, definition in _PROVIDER_MENU.items():
        status = "real" if definition["status"] == "ready" else "stub"
        console.print(f"  {option}. {definition['label']} [dim]({status})[/dim]")

    choice = Prompt.ask(
        "[bold cyan]Choice[/bold cyan]",
        choices=sorted(_PROVIDER_MENU.keys()),
        default="1",
    )
    selected = _PROVIDER_MENU[choice]
    return str(selected["provider"]), selected["mode"]


def _build_repl_prompt(user_prompt: str, history: list[tuple[str, str]]) -> str:
    if not history:
        return user_prompt

    recent_history = history[-_REPL_HISTORY_WINDOW:]
    transcript: list[str] = [
        "Continue the conversation naturally. The recent transcript so far is below.",
        "",
    ]
    for previous_user, previous_assistant in recent_history:
        transcript.append(f"User: {previous_user}")
        transcript.append(f"Assistant: {previous_assistant}")
    transcript.append(f"User: {user_prompt}")
    transcript.append("Assistant:")
    return "\n".join(transcript)


@contextmanager
def _spinner(text: str):
    with console.status(f"[bold green]{text}"):
        yield


if __name__ == "__main__":
    app()
