from __future__ import annotations

import hashlib
import hmac
import time
from typing import Any

from packages.chat.base import InboundChatEvent
from packages.domain.models import ConversationDomain, Project


class SlackSignatureVerifier:
    """Validate Slack request signatures for inbound HTTP events."""

    def __init__(self, signing_secret: str, max_age_seconds: int = 300) -> None:
        self._signing_secret = signing_secret.encode("utf-8")
        self._max_age_seconds = max_age_seconds

    def verify(self, body: bytes, timestamp: str | None, signature: str | None) -> bool:
        if not timestamp or not signature:
            return False
        if not signature.startswith("v0="):
            return False

        try:
            request_ts = int(timestamp)
        except ValueError:
            return False

        now = int(time.time())
        if abs(now - request_ts) > self._max_age_seconds:
            return False

        base_string = f"v0:{timestamp}:".encode("utf-8") + body
        expected = "v0=" + hmac.new(
            self._signing_secret,
            base_string,
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, signature)


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
        if event.get("bot_id"):
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
            metadata={
                "raw_event_type": event.get("type"),
                "event_id": payload.get("event_id"),
            },
        )

    def _resolve_logical_channel(self, project: Project, channel_id: str) -> ConversationDomain:
        for binding in project.channel_bindings.values():
            if binding.channel_id == channel_id:
                return binding.domain
        raise ValueError(
            f"Slack channel '{channel_id}' is not bound for project '{project.project_id}'."
        )
