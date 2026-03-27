from __future__ import annotations

from typing import Any

from packages.chat.base import InboundChatEvent
from packages.domain.models import ConversationDomain, Project


class DiscordEventTranslator:
    """Translate Discord-style inbound payloads into platform-neutral events."""

    def translate(self, project: Project, payload: dict[str, Any]) -> InboundChatEvent | None:
        event_type = str(payload.get("type", "message_create")).lower()
        if event_type not in {"message_create", "message"}:
            return None

        author = payload.get("author")
        if isinstance(author, dict) and author.get("bot"):
            return None

        channel_id = str(payload.get("channel_id", ""))
        logical_channel = self._resolve_logical_channel(project, channel_id)

        return InboundChatEvent(
            platform="discord",
            project_id=project.project_id,
            logical_channel=logical_channel,
            physical_channel_id=channel_id,
            sender_id=str((author or {}).get("id", "unknown")),
            sender_name=(author or {}).get("username"),
            content=str(payload.get("content", "")),
            message_id=str(payload.get("id", "")),
            thread_id=str(payload.get("thread_id") or "") or None,
            metadata={"raw_event_type": event_type},
        )

    def _resolve_logical_channel(self, project: Project, channel_id: str) -> ConversationDomain:
        for binding in project.channel_bindings.values():
            if binding.channel_id == channel_id:
                return binding.domain
        raise ValueError(
            f"Discord channel '{channel_id}' is not bound for project '{project.project_id}'."
        )
