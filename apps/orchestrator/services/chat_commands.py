from __future__ import annotations

from pydantic import BaseModel


class ParsedChatCommand(BaseModel):
    action: str
    target_id: str | None = None
    comment: str | None = None


class ChatCommandParser:
    """Parse platform-neutral user-control chat commands."""

    def parse(self, content: str) -> ParsedChatCommand | None:
        text = content.strip()
        if not text.startswith("/"):
            return None

        parts = text.split(maxsplit=2)
        command = parts[0].lower()

        if command == "/help":
            return ParsedChatCommand(action="help")

        if command == "/approvals":
            return ParsedChatCommand(action="list_approvals")

        if command == "/status":
            target_id = parts[1].strip() if len(parts) > 1 else None
            return ParsedChatCommand(action="task_status", target_id=target_id)

        if len(parts) < 2:
            return None

        target_id = parts[1].strip()
        comment = parts[2].strip() if len(parts) > 2 and parts[2].strip() else None

        if command == "/approve":
            return ParsedChatCommand(
                action="approve_approval",
                target_id=target_id,
                comment=comment,
            )
        if command == "/reject":
            return ParsedChatCommand(
                action="reject_approval",
                target_id=target_id,
                comment=comment,
            )
        return None
