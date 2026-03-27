from __future__ import annotations

import types

import pytest

from apps.orchestrator.slack.socket_mode import SlackSocketModeConfig, SlackSocketModeRuntime
from packages.domain.models import ChannelBinding, ConversationDomain, Project


def _make_project(project_id: str, chat_platform: str, channel_id: str) -> Project:
    return Project(
        project_id=project_id,
        name=project_id,
        repo_url=f"https://github.com/example/{project_id}",
        workspace_path=f"workspaces/{project_id}",
        chat_platform=chat_platform,
        channel_bindings={
            "user-control": ChannelBinding(
                domain=ConversationDomain.USER_CONTROL,
                channel_id=channel_id,
            )
        },
    )


class _FakeOrchestrator:
    def __init__(self, projects: list[Project]) -> None:
        self._projects = projects

    def list_projects(self) -> list[Project]:
        return self._projects


class _FakeIngress:
    def __init__(self) -> None:
        self.events = []

    async def handle_event(self, event):
        self.events.append(event)
        return types.SimpleNamespace(accepted=True)


@pytest.mark.anyio
async def test_socket_mode_runtime_disabled_without_app_token() -> None:
    runtime = SlackSocketModeRuntime(
        orchestrator=_FakeOrchestrator([]),  # type: ignore[arg-type]
        ingress=_FakeIngress(),  # type: ignore[arg-type]
        config=SlackSocketModeConfig(app_token=None, bot_token=None),
    )

    started = await runtime.start()

    assert started is False
    assert runtime.started is False


def test_socket_mode_runtime_resolves_project_by_channel_binding() -> None:
    slack_project = _make_project("slack-project", "slack", "C_USER_CONTROL")
    discord_project = _make_project("discord-project", "discord", "discord-user")

    runtime = SlackSocketModeRuntime(
        orchestrator=_FakeOrchestrator([discord_project, slack_project]),  # type: ignore[arg-type]
        ingress=_FakeIngress(),  # type: ignore[arg-type]
        config=SlackSocketModeConfig(app_token=None, bot_token=None),
    )

    resolved = runtime._resolve_project("C_USER_CONTROL")

    assert resolved is not None
    assert resolved.project_id == "slack-project"


@pytest.mark.anyio
async def test_socket_mode_runtime_processes_message_event_into_ingress() -> None:
    project = _make_project("sample-slack-project", "slack", "C_USER_CONTROL")
    ingress = _FakeIngress()
    runtime = SlackSocketModeRuntime(
        orchestrator=_FakeOrchestrator([project]),  # type: ignore[arg-type]
        ingress=ingress,  # type: ignore[arg-type]
        config=SlackSocketModeConfig(app_token=None, bot_token=None),
    )
    payload = {
        "type": "event_callback",
        "event": {
            "type": "message",
            "channel": "C_USER_CONTROL",
            "user": "U123",
            "text": "Run task from socket mode",
            "ts": "1710000000.000900",
        },
    }

    await runtime._process_event_payload(payload)

    assert len(ingress.events) == 1
    event = ingress.events[0]
    assert event.platform == "slack"
    assert event.project_id == "sample-slack-project"
    assert event.content == "Run task from socket mode"
