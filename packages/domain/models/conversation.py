from __future__ import annotations

from typing import Any

from pydantic import Field

from packages.domain.models.common import AuditRecord, ConversationDomain, PlatformBaseModel, new_id


class MessageEnvelope(PlatformBaseModel):
    platform: str
    channel_id: str
    thread_id: str | None = None
    message_id: str | None = None
    sender_id: str | None = None


class ConversationMessage(PlatformBaseModel):
    message_id: str = Field(default_factory=new_id)
    project_id: str
    domain: ConversationDomain
    role: str
    content: str
    envelope: MessageEnvelope | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ConversationThread(AuditRecord):
    conversation_id: str = Field(default_factory=new_id)
    project_id: str
    task_id: str | None = None
    domain: ConversationDomain
    title: str
    summary: str | None = None
    messages: list[ConversationMessage] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
