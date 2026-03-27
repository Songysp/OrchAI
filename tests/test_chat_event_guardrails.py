from __future__ import annotations

import pytest

from apps.orchestrator.discord.service import DiscordEventTranslator
from apps.orchestrator.services.chat_ingress_service import ChatIngressService
from apps.orchestrator.slack.service import SlackEventTranslator
from packages.chat.base import InboundChatEvent
from packages.domain.models import ChannelBinding, ConversationDomain, Project


@pytest.fixture(autouse=True)
def _reset_event_dedup_cache() -> None:
    ChatIngressService._seen_event_keys.clear()


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


@pytest.mark.anyio
async def test_ingress_ignores_duplicate_slack_event_ids() -> None:
    ingress = ChatIngressService(orchestrator=object())  # type: ignore[arg-type]
    event = InboundChatEvent(
        platform="slack",
        project_id="sample-slack-project",
        logical_channel=ConversationDomain.AI_OPS,
        physical_channel_id="C_AI_OPS",
        sender_id="U1",
        content="internal chatter",
        message_id="1710000000.001",
        metadata={"event_id": "Ev123"},
    )

    first = await ingress.handle_event(event)
    second = await ingress.handle_event(event)

    assert first.action == "ignored"
    assert second.action == "duplicate_ignored"


@pytest.mark.anyio
async def test_ingress_ignores_duplicate_discord_event_ids() -> None:
    ingress = ChatIngressService(orchestrator=object())  # type: ignore[arg-type]
    event = InboundChatEvent(
        platform="discord",
        project_id="sample-discord-project",
        logical_channel=ConversationDomain.AI_OPS,
        physical_channel_id="discord-ai-ops",
        sender_id="user-1",
        content="ops note",
        message_id="m-dup",
        metadata={"event_id": "m-dup"},
    )

    first = await ingress.handle_event(event)
    second = await ingress.handle_event(event)

    assert first.action == "ignored"
    assert second.action == "duplicate_ignored"


@pytest.mark.anyio
async def test_ingress_dedups_numeric_event_ids() -> None:
    ingress = ChatIngressService(orchestrator=object())  # type: ignore[arg-type]
    event = InboundChatEvent(
        platform="discord",
        project_id="sample-discord-project",
        logical_channel=ConversationDomain.AI_OPS,
        physical_channel_id="discord-ai-ops",
        sender_id="user-1",
        content="ops note",
        message_id=None,
        metadata={"event_id": 12345},
    )

    first = await ingress.handle_event(event)
    second = await ingress.handle_event(event)

    assert first.action == "ignored"
    assert second.action == "duplicate_ignored"


def test_slack_translator_ignores_bot_id_messages() -> None:
    translator = SlackEventTranslator()
    project = _make_project("sample-slack-project", "slack", "C_USER_CONTROL")

    translated = translator.translate(
        project,
        {
            "type": "event_callback",
            "event_id": "EvBot",
            "event": {
                "type": "message",
                "channel": "C_USER_CONTROL",
                "user": "U123",
                "bot_id": "B123",
                "text": "bot echo",
                "ts": "1710000000.010",
            },
        },
    )

    assert translated is None


def test_discord_translator_ignores_bot_id_messages() -> None:
    translator = DiscordEventTranslator()
    project = _make_project("sample-discord-project", "discord", "discord-user-control")

    translated = translator.translate(
        project,
        {
            "type": "message_create",
            "id": "m-bot",
            "channel_id": "discord-user-control",
            "content": "bot echo",
            "bot_id": "application-bot-id",
            "author": {"id": "user-1", "username": "bot", "bot": False},
        },
    )

    assert translated is None
