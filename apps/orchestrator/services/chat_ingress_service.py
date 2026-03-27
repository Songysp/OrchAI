from __future__ import annotations

from pydantic import BaseModel

from apps.orchestrator.services.chat_commands import ChatCommandParser
from apps.orchestrator.services.orchestrator_service import OrchestratorService
from apps.orchestrator.workflows.representative import TaskRunResult
from packages.chat.base import InboundChatEvent
from packages.domain.models import ConversationDomain


class ChatIngressResult(BaseModel):
    accepted: bool
    action: str
    message: str
    task_result: TaskRunResult | None = None
    approval_id: str | None = None
    task_id: str | None = None
    task_status: str | None = None
    resumed: bool = False


class ChatIngressService:
    """Platform-neutral ingress coordinator for chat-triggered actions."""

    def __init__(self, orchestrator: OrchestratorService) -> None:
        self.orchestrator = orchestrator
        self.command_parser = ChatCommandParser()

    async def handle_event(self, event: InboundChatEvent) -> ChatIngressResult:
        if event.logical_channel != ConversationDomain.USER_CONTROL:
            return ChatIngressResult(
                accepted=True,
                action="ignored",
                message=(
                    f"Ignored inbound {event.platform} event for logical channel "
                    f"'{event.logical_channel.value}'."
                ),
            )

        command = self.command_parser.parse(event.content)
        if command is not None:
            return await self._handle_command(event, command.action, command.target_id, command.comment)

        task_result = await self.orchestrator.handle_user_control_message(
            project_id=event.project_id,
            user_input=event.content,
        )
        return ChatIngressResult(
            accepted=True,
            action="task_created",
            message=f"Created and ran task {task_result.task_id} from {event.platform} inbound message.",
            task_result=task_result,
            task_id=task_result.task_id,
            task_status=task_result.final_status.value,
        )

    async def _handle_command(
        self,
        event: InboundChatEvent,
        action: str,
        target_id: str | None,
        comment: str | None,
    ) -> ChatIngressResult:
        actor = event.sender_name or event.sender_id
        project = self.orchestrator.get_project(event.project_id)
        if project is None:
            raise ValueError(f"Project '{event.project_id}' was not found.")
        chat_adapter = self.orchestrator.runtime.get_chat_adapter(project)

        if action == "help":
            help_message = (
                "Available commands: /help, /approvals, /status <task_id>, "
                "/approve <approval_id> [comment], /reject <approval_id> [comment]."
            )
            await chat_adapter.post_user_message(project, help_message)
            return ChatIngressResult(
                accepted=True,
                action="help",
                message=help_message,
            )

        if action == "list_approvals":
            approvals = [
                approval
                for approval in self.orchestrator.list_approvals(project.project_id)
                if approval.status.value == "pending"
            ]
            if approvals:
                message = "Pending approvals: " + ", ".join(
                    f"{approval.approval_id} (task {approval.task_id})" for approval in approvals[:10]
                )
            else:
                message = "There are no pending approvals for this project."
            await chat_adapter.post_user_message(project, message)
            return ChatIngressResult(
                accepted=True,
                action="approvals_listed",
                message=message,
            )

        if action == "task_status":
            if not target_id:
                message = "Usage: /status <task_id>"
                await chat_adapter.post_user_message(project, message)
                return ChatIngressResult(
                    accepted=False,
                    action="status_usage",
                    message=message,
                )
            status = self.orchestrator.get_task_status(target_id)
            if status is None or status.project_id != project.project_id:
                message = f"Task '{target_id}' was not found in project '{project.project_id}'."
                await chat_adapter.post_user_message(project, message)
                return ChatIngressResult(
                    accepted=False,
                    action="task_not_found",
                    message=message,
                    task_id=target_id,
                )
            message = (
                f"Task {status.task_id} is {status.status.value} at stage {status.stage.value}. "
                f"Summary: {status.summary or 'No summary yet.'}"
            )
            await chat_adapter.post_user_message(project, message)
            return ChatIngressResult(
                accepted=True,
                action="task_status",
                message=message,
                task_id=status.task_id,
                task_status=status.status.value,
            )

        if action == "approve_approval":
            if not target_id:
                return ChatIngressResult(
                    accepted=False,
                    action="approval_usage",
                    message="Usage: /approve <approval_id> [comment]",
                )
            result = await self.orchestrator.approve_approval(
                approval_id=target_id,
                approved_by=actor,
                comment=comment,
                resume_task=True,
            )
            if result is None:
                return ChatIngressResult(
                    accepted=False,
                    action="approval_not_found",
                    message=f"Approval '{target_id}' was not found.",
                    approval_id=target_id,
                )
            await chat_adapter.post_user_message(
                project,
                (
                    f"Approval {target_id} approved by {actor}. "
                    f"Task {result['task'].task_id} is now {result['task'].status.value}."
                ),
            )
            await chat_adapter.post_ops_log(
                project,
                f"Approval {target_id} approved via {event.platform} inbound command.",
            )
            return ChatIngressResult(
                accepted=True,
                action="approval_approved",
                message=f"Approval '{target_id}' was approved.",
                approval_id=result["approval"].approval_id,
                task_id=result["task"].task_id,
                task_status=result["task"].status.value,
                resumed=bool(result["resumed"]),
            )

        if action == "reject_approval":
            if not target_id:
                return ChatIngressResult(
                    accepted=False,
                    action="rejection_usage",
                    message="Usage: /reject <approval_id> [comment]",
                )
            result = self.orchestrator.reject_approval(
                approval_id=target_id,
                approved_by=actor,
                comment=comment,
            )
            if result is None:
                return ChatIngressResult(
                    accepted=False,
                    action="approval_not_found",
                    message=f"Approval '{target_id}' was not found.",
                    approval_id=target_id,
                )
            await chat_adapter.post_user_message(
                project,
                (
                    f"Approval {target_id} rejected by {actor}. "
                    f"Task {result['task'].task_id} is now {result['task'].status.value}."
                ),
            )
            await chat_adapter.post_ops_log(
                project,
                f"Approval {target_id} rejected via {event.platform} inbound command.",
            )
            return ChatIngressResult(
                accepted=True,
                action="approval_rejected",
                message=f"Approval '{target_id}' was rejected.",
                approval_id=result["approval"].approval_id,
                task_id=result["task"].task_id,
                task_status=result["task"].status.value,
                resumed=False,
            )

        return ChatIngressResult(
            accepted=False,
            action="unsupported_command",
            message=f"Unsupported command action '{action}'.",
            approval_id=target_id,
        )
