from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field

from packages.domain.models import ConversationDomain, MessageEnvelope, Project


class IncomingChatEvent(BaseModel):
    project_id: str
    domain: ConversationDomain
    sender_id: str
    content: str
    envelope: MessageEnvelope
    metadata: dict[str, Any] = Field(default_factory=dict)


class OutgoingChatMessage(BaseModel):
    project_id: str
    domain: ConversationDomain
    content: str
    thread_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ChatAdapter(ABC):
    platform_name: str

    @abstractmethod
    def supports_project(self, project: Project) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def send_message(self, project: Project, message: OutgoingChatMessage) -> MessageEnvelope:
        raise NotImplementedError

    @abstractmethod
    async def post_log(self, project: Project, domain: ConversationDomain, content: str) -> MessageEnvelope:
        raise NotImplementedError

    @abstractmethod
    async def post_approval_request(self, project: Project, content: str) -> MessageEnvelope:
        raise NotImplementedError
