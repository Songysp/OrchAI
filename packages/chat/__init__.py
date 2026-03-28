"""Chat transport abstractions. Platform adapters (Slack, Discord) removed — CLI-First design."""

from packages.chat.base import ChatAdapter, ChatDelivery, ChatMessage

__all__ = [
    "ChatAdapter",
    "ChatDelivery",
    "ChatMessage",
]
