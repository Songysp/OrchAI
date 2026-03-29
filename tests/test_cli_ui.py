from __future__ import annotations

import asyncio
from io import StringIO

from rich.console import Console
from typer.testing import CliRunner

from apps.cli import main, ui
from packages.agents.drivers.claude_cli import ClaudeCLIQuotaError
from packages.agents.errors import ProviderAPIError, ProviderRateLimitError
from packages.domain.models.project import Project
from packages.domain.models.turn import TurnResult


runner = CliRunner()


def test_chat_command_invokes_async_runner(monkeypatch):
    captured: dict[str, object] = {}

    async def fake_run_single_turn(
        prompt: str,
        provider: str | None,
        model: str | None,
        mode: str | None,
        *,
        show_banner: bool = True,
    ) -> None:
        captured["prompt"] = prompt
        captured["provider"] = provider
        captured["model"] = model
        captured["mode"] = mode
        captured["show_banner"] = show_banner

    monkeypatch.setattr(main, "_run_single_turn", fake_run_single_turn)

    result = runner.invoke(main.app, ["chat", "ship it", "--model", "claude-3", "--mode", "api"])

    assert result.exit_code == 0
    assert captured == {
        "prompt": "ship it",
        "provider": None,
        "model": "claude-3",
        "mode": "api",
        "show_banner": True,
    }


def test_orchestrate_command_invokes_async_runner(monkeypatch):
    captured: dict[str, object] = {}

    async def fake_run_full_orchestration(
        prompt: str,
        provider: str | None,
        model: str | None,
        mode: str | None,
        max_turns: int,
    ) -> None:
        captured["prompt"] = prompt
        captured["provider"] = provider
        captured["model"] = model
        captured["mode"] = mode
        captured["max_turns"] = max_turns

    monkeypatch.setattr(main, "_run_full_orchestration", fake_run_full_orchestration)

    result = runner.invoke(
        main.app,
        ["orchestrate", "build feature", "--model", "claude-3", "--mode", "cli", "--max-turns", "7"],
    )

    assert result.exit_code == 0
    assert captured == {
        "prompt": "build feature",
        "provider": None,
        "model": "claude-3",
        "mode": "cli",
        "max_turns": 7,
    }


def test_orchestrate_command_handles_claude_quota_error(monkeypatch):
    async def fake_run_full_orchestration(
        prompt: str,
        provider: str | None,
        model: str | None,
        mode: str | None,
        max_turns: int,
    ) -> None:
        raise ClaudeCLIQuotaError(
            "Claude CLI error (code 1): You've hit your limit · resets 7pm (Asia/Seoul)",
            reset_at="7pm (Asia/Seoul)",
        )

    monkeypatch.setattr(main, "_run_full_orchestration", fake_run_full_orchestration)

    result = runner.invoke(main.app, ["orchestrate", "build feature"])

    assert result.exit_code == 1
    assert "Claude CLI usage limit reached." in result.output
    assert "Reset:" in result.output
    assert "7pm" in result.output
    assert "Asia/Seoul" in result.output
    assert "Traceback" not in result.output


def test_chat_command_handles_provider_rate_limit(monkeypatch):
    async def fake_run_single_turn(
        prompt: str,
        provider: str | None,
        model: str | None,
        mode: str | None,
        *,
        show_banner: bool = True,
    ) -> None:
        raise ProviderRateLimitError("gemini", "Gemini API rate limit reached (429): limit", status_code=429)

    monkeypatch.setattr(main, "_run_single_turn", fake_run_single_turn)

    result = runner.invoke(main.app, ["chat", "hello", "--provider", "gemini"])

    assert result.exit_code == 1
    assert "Gemini API rate limit reached." in result.output
    assert "429" in result.output


def test_chat_command_handles_provider_api_error(monkeypatch):
    async def fake_run_single_turn(
        prompt: str,
        provider: str | None,
        model: str | None,
        mode: str | None,
        *,
        show_banner: bool = True,
    ) -> None:
        raise ProviderAPIError("codex", "OpenAI Responses API call failed (401): bad key", status_code=401)

    monkeypatch.setattr(main, "_run_single_turn", fake_run_single_turn)

    result = runner.invoke(main.app, ["chat", "hello", "--provider", "codex"])

    assert result.exit_code == 1
    assert "Codex API request failed." in result.output
    assert "401" in result.output


def test_root_command_invokes_repl(monkeypatch):
    captured: dict[str, object] = {}

    async def fake_run_repl(provider: str | None, model: str | None, mode: str | None) -> None:
        captured["provider"] = provider
        captured["model"] = model
        captured["mode"] = mode

    monkeypatch.setattr(main, "_run_repl", fake_run_repl)

    result = runner.invoke(main.app, [])

    assert result.exit_code == 0
    assert captured == {"provider": None, "model": None, "mode": None}


def test_build_repl_prompt_includes_history() -> None:
    prompt = main._build_repl_prompt(
        "그리고 넌 누구냐",
        [("안녕", "안녕하세요. OrchAI입니다.")],
    )

    assert "Continue the conversation naturally." in prompt
    assert "User: 안녕" in prompt
    assert "Assistant: 안녕하세요. OrchAI입니다." in prompt
    assert "User: 그리고 넌 누구냐" in prompt
    assert prompt.endswith("Assistant:")


def test_build_repl_prompt_limits_history_window() -> None:
    history = [(f"user-{idx}", f"assistant-{idx}") for idx in range(8)]

    prompt = main._build_repl_prompt("latest", history)

    assert "user-0" not in prompt
    assert "assistant-0" not in prompt
    assert "user-1" not in prompt
    assert "assistant-1" not in prompt
    assert "user-2" in prompt
    assert "assistant-7" in prompt


def test_run_repl_clear_resets_history(monkeypatch):
    prompts = iter(["first", "/clear", "second", "/exit"])
    sent_prompts: list[str] = []
    rendered_outputs: list[str] = []

    monkeypatch.setattr(main, "display_banner", lambda: None)
    monkeypatch.setattr(main, "_build_worker_runtime", lambda provider, model, mode: ("adapter", "selection"))
    monkeypatch.setattr(main.Prompt, "ask", lambda _: next(prompts))
    monkeypatch.setattr(main, "_display_worker_result", lambda output: rendered_outputs.append(output))

    async def fake_run_worker_turn(adapter, selection, prompt: str, *, project_id: str):
        sent_prompts.append(prompt)
        return type("Result", (), {"output": f"reply:{len(sent_prompts)}"})()

    monkeypatch.setattr(main, "_run_worker_turn", fake_run_worker_turn)

    asyncio.run(main._run_repl(None, None, None))

    assert sent_prompts[0] == "first"
    assert sent_prompts[1] == "second"
    assert "first" not in sent_prompts[1]
    assert rendered_outputs == ["reply:1", "reply:2"]


def test_resolve_provider_choice_from_prompt(monkeypatch):
    monkeypatch.setattr(main.Prompt, "ask", lambda *args, **kwargs: "4")

    provider, mode = main._resolve_provider_choice(None, None)

    assert provider == "codex"
    assert mode is None


def test_resolve_provider_choice_maps_claude_api_prompt(monkeypatch):
    monkeypatch.setattr(main.Prompt, "ask", lambda *args, **kwargs: "2")

    provider, mode = main._resolve_provider_choice(None, None)

    assert provider == "claude"
    assert mode == "api"


class _StatusRecorder:
    def __init__(self, owner: "_ConsoleRecorder", message: str, spinner: str | None):
        self.owner = owner
        self.message = message
        self.spinner = spinner
        self.updates: list[str] = []
        self.start_calls = 0
        self.stop_calls = 0

    def __enter__(self) -> "_StatusRecorder":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def stop(self) -> None:
        self.stop_calls += 1

    def start(self) -> None:
        self.start_calls += 1

    def update(self, message: str) -> None:
        self.updates.append(message)


class _ConsoleRecorder:
    def __init__(self):
        self.print_calls: list[tuple[tuple[object, ...], dict[str, object]]] = []
        self.status_contexts: list[_StatusRecorder] = []

    def print(self, *args, **kwargs) -> None:
        self.print_calls.append((args, kwargs))

    def status(self, message: str, spinner: str | None = None) -> _StatusRecorder:
        ctx = _StatusRecorder(self, message, spinner)
        self.status_contexts.append(ctx)
        return ctx


def test_orchestration_uses_rich_spinner(monkeypatch):
    class FakeHiveOrchestrator:
        def __init__(self, adapter, max_turns: int):
            self.adapter = adapter
            self.max_turns = max_turns

        async def execute_stream(self, prompt: str, project: Project):
            yield TurnResult(
                turn_id="p0",
                run_id="run_1",
                turn_index=0,
                role="planner",
                prompt=prompt,
                output="Plan ready",
            )
            yield TurnResult(
                turn_id="w1",
                run_id="run_1",
                turn_index=1,
                role="worker",
                prompt=prompt,
                output="Implemented",
            )
            yield TurnResult(
                turn_id="r1",
                run_id="run_1",
                turn_index=2,
                role="refiner",
                prompt=prompt,
                output="DONE",
            )

    console = _ConsoleRecorder()
    rendered_results: list[tuple[str, str]] = []

    monkeypatch.setattr(main, "console", console)
    monkeypatch.setattr(main, "display_banner", lambda: None)
    monkeypatch.setattr(main, "display_result", lambda role, output: rendered_results.append((role, output)))
    monkeypatch.setattr(main, "_build_worker_runtime", lambda provider, model, mode: ("adapter", "selection"))
    monkeypatch.setattr(main, "HiveOrchestrator", FakeHiveOrchestrator)

    asyncio.run(main._run_full_orchestration("Audit the repo", None, None, None, max_turns=3))

    assert len(console.status_contexts) == 1
    status = console.status_contexts[0]
    assert status.message == "[bold cyan]Planner is analyzing...[/bold cyan]"
    assert status.spinner == "dots"
    assert status.stop_calls == 3
    assert status.start_calls == 2
    assert status.updates == [
        "[bold cyan]Worker is implementing...[/bold cyan]",
        "[bold cyan]Refiner is reviewing...[/bold cyan]",
    ]
    assert rendered_results == [
        ("planner", "Plan ready"),
        ("worker", "Implemented"),
        ("refiner", "DONE"),
    ]


def test_display_result_renders_output_table(monkeypatch):
    buffer = StringIO()
    console = Console(file=buffer, force_terminal=False, width=80)

    monkeypatch.setattr(ui, "console", console)

    ui.display_result("worker", "Implemented feature X")

    rendered = buffer.getvalue()

    assert "WORKER" in rendered
    assert "Implemented feature X" in rendered
    assert "-" * 30 in rendered
