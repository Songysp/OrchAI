from __future__ import annotations

import asyncio
from io import StringIO

from rich.console import Console
from typer.testing import CliRunner

from apps.cli import main, ui
from packages.domain.models.project import Project
from packages.domain.models.turn import TurnResult


runner = CliRunner()


def test_chat_command_invokes_async_runner(monkeypatch):
    captured: dict[str, object] = {}

    async def fake_run_single_turn(prompt: str, model: str | None, mode: str | None) -> None:
        captured["prompt"] = prompt
        captured["model"] = model
        captured["mode"] = mode

    monkeypatch.setattr(main, "_run_single_turn", fake_run_single_turn)

    result = runner.invoke(main.app, ["chat", "ship it", "--model", "claude-3", "--mode", "api"])

    assert result.exit_code == 0
    assert captured == {
        "prompt": "ship it",
        "model": "claude-3",
        "mode": "api",
    }


def test_orchestrate_command_invokes_async_runner(monkeypatch):
    captured: dict[str, object] = {}

    async def fake_run_full_orchestration(
        prompt: str,
        model: str | None,
        mode: str | None,
        max_turns: int,
    ) -> None:
        captured["prompt"] = prompt
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
        "model": "claude-3",
        "mode": "cli",
        "max_turns": 7,
    }


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
    monkeypatch.setattr(main, "ConfigService", lambda config: object())
    monkeypatch.setattr(main.ConfigLoader, "load", lambda self: {})
    monkeypatch.setattr(main, "ClaudeAdapter", lambda config_service: object())
    monkeypatch.setattr(main, "HiveOrchestrator", FakeHiveOrchestrator)

    asyncio.run(main._run_full_orchestration("Audit the repo", None, None, max_turns=3))

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
