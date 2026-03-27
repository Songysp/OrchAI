from __future__ import annotations

from packages.chat.base import ChatAdapter, OutgoingChatMessage
from packages.domain.models import ConversationDomain, MessageEnvelope, Project


class DiscordAdapter(ChatAdapter):
    platform_name = "discord"

    def supports_project(self, project: Project) -> bool:
        return project.chat_platform.lower() == self.platform_name

    async def send_message(self, project: Project, message: OutgoingChatMessage) -> MessageEnvelope:
        binding = project.channel_bindings[message.domain]
        return MessageEnvelope(platform=self.platform_name, channel_id=binding.channel_id, thread_id=message.thread_id)

    async def post_log(self, project: Project, domain: ConversationDomain, content: str) -> MessageEnvelope:
        binding = project.channel_bindings[domain]
        return MessageEnvelope(platform=self.platform_name, channel_id=binding.channel_id)

    async def post_approval_request(self, project: Project, content: str) -> MessageEnvelope:
        binding = project.channel_bindings[ConversationDomain.USER_CONTROL]
        return MessageEnvelope(platform=self.platform_name, channel_id=binding.channel_id)
