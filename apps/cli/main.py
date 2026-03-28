from __future__ import annotations

import asyncio
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Optional

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import typer

from apps.cli.ui import console, display_banner, display_config, display_result, display_status
from packages.agents.base import AgentSelection, AgentTurnRequest
from packages.agents.claude_adapter import ClaudeAdapter
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


# ── Commands ──────────────────────────────────────────────────────────────────

@app.command()
def chat(
    prompt: str = typer.Argument(..., help="The prompt for the AI"),
    model: Optional[str] = typer.Option(None, help="Model override"),
    mode: Optional[str] = typer.Option(None, help="Driver mode: cli or api"),
):
    """Single-turn conversation with the AI worker."""
    asyncio.run(_run_single_turn(prompt, model, mode))


@app.command()
def orchestrate(
    prompt: str = typer.Argument(..., help="Complex task for the AI team"),
    model: Optional[str] = typer.Option(None, help="Model override"),
    mode: Optional[str] = typer.Option(None, help="Driver mode: cli or api"),
    max_turns: int = typer.Option(5, help="Maximum Planner→Worker→Refiner cycles"),
):
    """Full autonomous Planner → Worker → Refiner orchestration loop."""
    asyncio.run(_run_full_orchestration(prompt, model, mode, max_turns))


# ── Async runners ─────────────────────────────────────────────────────────────

async def _run_single_turn(prompt: str, model: Optional[str], mode: Optional[str]) -> None:
    display_banner()

    root_path = Path(".")
    config_service = ConfigService(ConfigLoader(root_path).load())
    params = {"driver_mode": mode} if mode else {}
    resolved = config_service.resolve_claude_config(parameters=params, model=model)

    display_config({
        "model": resolved.model,
        "driver_mode": resolved.mode,
        "cli_command": resolved.cli_command,
        "timeout": resolved.timeout,
        "status": "ready",
    })

    mock_project = Project(
        project_id="cli-single-turn",
        repo_url="https://github.com/OrchAI",
        workspace_path=".",
        chat_platform="cli",
    )

    adapter = ClaudeAdapter(config_service=config_service)
    selection = AgentSelection(role="worker", provider="claude", model=model, parameters=params)
    request = AgentTurnRequest(
        project=mock_project,
        role="worker",
        prompt=prompt,
        agent_selection=selection,
    )

    display_status("OrchAI", f"Sending prompt to Claude")
    with _spinner("Waiting for Claude response..."):
        result = await adapter.run_turn(request)

    display_result(result.role, result.output)


async def _run_full_orchestration(
    prompt: str,
    model: Optional[str],
    mode: Optional[str],
    max_turns: int,
) -> None:
    display_banner()

    root_path = Path(".")
    config_service = ConfigService(ConfigLoader(root_path).load())

    project = Project(
        project_id="hive-orchestration",
        repo_url="https://github.com/OrchAI",
        workspace_path=".",
        chat_platform="cli",
    )

    adapter = ClaudeAdapter(config_service=config_service)
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


@contextmanager
def _spinner(text: str):
    with console.status(f"[bold green]{text}"):
        yield


if __name__ == "__main__":
    app()
