import pytest

from packages.chat import DiscordAdapter, SlackAdapter
from packages.domain.models import ChannelBinding, ConversationDomain, Project


@pytest.mark.anyio
async def test_slack_adapter_resolves_logical_channel_binding() -> None:
    project = Project(
        project_id="project-slack",
        repo_url="https://github.com/example/project-slack",
        workspace_path="workspaces/project-slack",
        chat_platform="slack",
        channel_bindings={
            "ai-ops": ChannelBinding(domain=ConversationDomain.AI_OPS, channel_id="C_OPS"),
            "ai-council": ChannelBinding(domain=ConversationDomain.AI_COUNCIL, channel_id="C_COUNCIL"),
            "user-control": ChannelBinding(domain=ConversationDomain.USER_CONTROL, channel_id="C_USER"),
        },
    )

    delivery = await SlackAdapter().post_ops_log(project, "Task started")

    assert delivery.platform == "slack"
    assert delivery.logical_channel == ConversationDomain.AI_OPS
    assert delivery.physical_channel_id == "C_OPS"


@pytest.mark.anyio
async def test_discord_adapter_resolves_logical_channel_binding() -> None:
    project = Project(
        project_id="project-discord",
        repo_url="https://github.com/example/project-discord",
        workspace_path="workspaces/project-discord",
        chat_platform="discord",
        channel_bindings={
            "ai-ops": ChannelBinding(domain=ConversationDomain.AI_OPS, channel_id="discord-ops"),
            "ai-council": ChannelBinding(domain=ConversationDomain.AI_COUNCIL, channel_id="discord-council"),
            "user-control": ChannelBinding(domain=ConversationDomain.USER_CONTROL, channel_id="discord-user"),
        },
    )

    delivery = await DiscordAdapter().post_council_message(project, "Planner proposes option A")

    assert delivery.platform == "discord"
    assert delivery.logical_channel == ConversationDomain.AI_COUNCIL
    assert delivery.physical_channel_id == "discord-council"
