from __future__ import annotations

from typing import Any

from packages.chat.base import InboundChatEvent
from packages.domain.models import ConversationDomain, Project


class SlackEventTranslator:
    """Translate Slack-style inbound payloads into platform-neutral events."""

    def translate(self, project: Project, payload: dict[str, Any]) -> InboundChatEvent | None:
        if payload.get("type") == "url_verification":
            return None

        event = payload.get("event")
        if not isinstance(event, dict):
            return None
        if event.get("type") != "message":
            return None
        if event.get("subtype") == "bot_message":
            return None

        channel_id = str(event.get("channel", ""))
        logical_channel = self._resolve_logical_channel(project, channel_id)

        return InboundChatEvent(
            platform="slack",
            project_id=project.project_id,
            logical_channel=logical_channel,
            physical_channel_id=channel_id,
            sender_id=str(event.get("user", "unknown")),
            content=str(event.get("text", "")),
            message_id=str(event.get("client_msg_id") or event.get("ts") or ""),
            thread_id=str(event.get("thread_ts") or "") or None,
            metadata={"raw_event_type": event.get("type")},
        )

    def _resolve_logical_channel(self, project: Project, channel_id: str) -> ConversationDomain:
        for binding in project.channel_bindings.values():
            if binding.channel_id == channel_id:
                return binding.domain
        raise ValueError(
            f"Slack channel '{channel_id}' is not bound for project '{project.project_id}'."
        )
