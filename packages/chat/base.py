from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field

from packages.domain.models import ConversationDomain, Project


class ChatMessage(BaseModel):
    """Platform-neutral message payload.

    A logical channel identifies the intent domain in the platform
    (`ai-council`, `ai-ops`, `user-control`), while adapters resolve the
    actual Slack channel ID or Discord channel/thread target.
    """

    project_id: str
    logical_channel: ConversationDomain
    content: str
    thread_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ChatDelivery(BaseModel):
    """Platform-neutral delivery result returned by adapters."""

    platform: str
    logical_channel: ConversationDomain
    physical_channel_id: str
    message_id: str | None = None
    thread_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class InboundChatEvent(BaseModel):
    """Platform-neutral inbound chat event.

    Transport-specific HTTP or gateway payloads are normalized into this
    shape before application services decide what orchestration action to take.
    """

    platform: str
    project_id: str
    logical_channel: ConversationDomain
    physical_channel_id: str
    sender_id: str
    sender_name: str | None = None
    content: str
    message_id: str | None = None
    thread_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ChatAdapter(ABC):
    platform_name: str

    @abstractmethod
    def supports_project(self, project: Project) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def send_message(self, project: Project, message: ChatMessage) -> ChatDelivery:
        raise NotImplementedError

    @abstractmethod
    async def send_thread_reply(
        self,
        project: Project,
        message: ChatMessage,
        parent_message_id: str,
    ) -> ChatDelivery:
        raise NotImplementedError

    @abstractmethod
    async def post_approval_request(
        self,
        project: Project,
        content: str,
        thread_id: str | None = None,
    ) -> ChatDelivery:
        raise NotImplementedError

    @abstractmethod
    async def post_ops_log(
        self,
        project: Project,
        content: str,
        thread_id: str | None = None,
    ) -> ChatDelivery:
        raise NotImplementedError

    @abstractmethod
    async def post_council_message(
        self,
        project: Project,
        content: str,
        thread_id: str | None = None,
    ) -> ChatDelivery:
        raise NotImplementedError

    @abstractmethod
    async def post_user_message(
        self,
        project: Project,
        content: str,
        thread_id: str | None = None,
    ) -> ChatDelivery:
        raise NotImplementedError

    def _binding_for(self, project: Project, logical_channel: ConversationDomain):
        binding = project.channel_bindings.get(logical_channel.value)
        if binding is None:
            raise ValueError(
                f"Project '{project.project_id}' does not define a binding for logical channel '{logical_channel.value}'."
            )
        return binding
