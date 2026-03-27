from __future__ import annotations

from packages.chat.base import ChatAdapter, ChatDelivery, ChatMessage
from packages.domain.models import ConversationDomain, Project


class DiscordAdapter(ChatAdapter):
    """Placeholder Discord transport adapter.

    Future implementation should encapsulate Discord-specific channel,
    thread, and gateway behavior inside this adapter.
    """

    platform_name = "discord"

    def supports_project(self, project: Project) -> bool:
        return project.chat_platform.lower() == self.platform_name

    async def send_message(self, project: Project, message: ChatMessage) -> ChatDelivery:
        binding = self._binding_for(project, message.logical_channel)
        return ChatDelivery(
            platform=self.platform_name,
            logical_channel=message.logical_channel,
            physical_channel_id=binding.channel_id,
            thread_id=message.thread_id,
            metadata={"delivery_mode": "placeholder", "thread_enabled": binding.thread_enabled},
        )

    async def send_thread_reply(
        self,
        project: Project,
        message: ChatMessage,
        parent_message_id: str,
    ) -> ChatDelivery:
        binding = self._binding_for(project, message.logical_channel)
        return ChatDelivery(
            platform=self.platform_name,
            logical_channel=message.logical_channel,
            physical_channel_id=binding.channel_id,
            thread_id=message.thread_id or parent_message_id,
            metadata={
                "delivery_mode": "placeholder",
                "reply_to_message_id": parent_message_id,
                "thread_enabled": binding.thread_enabled,
            },
        )

    async def post_approval_request(
        self,
        project: Project,
        content: str,
        thread_id: str | None = None,
    ) -> ChatDelivery:
        return await self.send_message(
            project,
            ChatMessage(
                project_id=project.project_id,
                logical_channel=ConversationDomain.USER_CONTROL,
                content=content,
                thread_id=thread_id,
            ),
        )

    async def post_ops_log(
        self,
        project: Project,
        content: str,
        thread_id: str | None = None,
    ) -> ChatDelivery:
        return await self.send_message(
            project,
            ChatMessage(
                project_id=project.project_id,
                logical_channel=ConversationDomain.AI_OPS,
                content=content,
                thread_id=thread_id,
            ),
        )

    async def post_council_message(
        self,
        project: Project,
        content: str,
        thread_id: str | None = None,
    ) -> ChatDelivery:
        return await self.send_message(
            project,
            ChatMessage(
                project_id=project.project_id,
                logical_channel=ConversationDomain.AI_COUNCIL,
                content=content,
                thread_id=thread_id,
            ),
        )

    async def post_user_message(
        self,
        project: Project,
        content: str,
        thread_id: str | None = None,
    ) -> ChatDelivery:
        return await self.send_message(
            project,
            ChatMessage(
                project_id=project.project_id,
                logical_channel=ConversationDomain.USER_CONTROL,
                content=content,
                thread_id=thread_id,
            ),
        )
