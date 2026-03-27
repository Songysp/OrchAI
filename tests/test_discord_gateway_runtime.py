from __future__ import annotations

import asyncio
import types

import pytest

from apps.orchestrator.discord.gateway import DiscordGatewayConfig, DiscordGatewayRuntime
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


class _FakeGatewayClient:
    def __init__(self) -> None:
        self.handler = None
        self.closed = False

    def set_message_handler(self, handler):
        self.handler = handler

    async def start(self, _token: str) -> None:
        while not self.closed:
            await asyncio.sleep(0.01)

    async def close(self) -> None:
        self.closed = True


@pytest.mark.anyio
async def test_discord_gateway_runtime_disabled_without_bot_token() -> None:
    runtime = DiscordGatewayRuntime(
        orchestrator=_FakeOrchestrator([]),  # type: ignore[arg-type]
        ingress=_FakeIngress(),  # type: ignore[arg-type]
        config=DiscordGatewayConfig(bot_token=None),
    )

    started = await runtime.start()

    assert started is False
    assert runtime.started is False


def test_discord_gateway_runtime_resolves_project_by_channel_binding() -> None:
    slack_project = _make_project("slack-project", "slack", "C_USER_CONTROL")
    discord_project = _make_project("discord-project", "discord", "discord-user")

    runtime = DiscordGatewayRuntime(
        orchestrator=_FakeOrchestrator([slack_project, discord_project]),  # type: ignore[arg-type]
        ingress=_FakeIngress(),  # type: ignore[arg-type]
        config=DiscordGatewayConfig(bot_token=None),
    )

    resolved = runtime._resolve_project("discord-user")

    assert resolved is not None
    assert resolved.project_id == "discord-project"


@pytest.mark.anyio
async def test_discord_gateway_runtime_processes_message_event_into_ingress() -> None:
    project = _make_project("sample-discord-project", "discord", "discord-user-control")
    ingress = _FakeIngress()
    runtime = DiscordGatewayRuntime(
        orchestrator=_FakeOrchestrator([project]),  # type: ignore[arg-type]
        ingress=ingress,  # type: ignore[arg-type]
        config=DiscordGatewayConfig(bot_token=None),
    )
    payload = {
        "type": "message_create",
        "id": "m-100",
        "channel_id": "discord-user-control",
        "content": "Run task from discord gateway",
        "author": {"id": "user-10", "username": "song", "bot": False},
    }

    await runtime._process_message_payload(payload)

    assert len(ingress.events) == 1
    event = ingress.events[0]
    assert event.platform == "discord"
    assert event.project_id == "sample-discord-project"
    assert event.content == "Run task from discord gateway"


@pytest.mark.anyio
async def test_discord_gateway_runtime_start_and_stop_with_fake_client() -> None:
    fake_client = _FakeGatewayClient()
    runtime = DiscordGatewayRuntime(
        orchestrator=_FakeOrchestrator([]),  # type: ignore[arg-type]
        ingress=_FakeIngress(),  # type: ignore[arg-type]
        config=DiscordGatewayConfig(bot_token="discord-token"),
        client_factory=lambda _config: fake_client,
    )

    started = await runtime.start()
    assert started is True
    assert runtime.started is True
    assert runtime.runner_task is not None
    assert fake_client.handler is not None

    await runtime.stop()

    assert fake_client.closed is True
    assert runtime.started is False
    assert runtime.runner_task is None
