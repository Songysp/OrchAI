from __future__ import annotations

from pydantic import BaseModel

from apps.orchestrator.services.project_runtime import ProjectRuntime
from apps.orchestrator.workflows.representative import RepresentativeWorkflow, TaskRunResult
from packages.domain.models import (
    Approval,
    ApprovalStatus,
    ConversationMessage,
    ConversationThread,
    ConversationDomain,
    Decision,
    MessageEnvelope,
    Task,
    TaskStage,
    TaskStatus,
)
from packages.domain.services import DecisionService, TaskService, TaskStatusView
from packages.domain.services.registry import PlatformRegistry


class CreateTaskInput(BaseModel):
    project_id: str
    user_input: str


class CreateTaskResult(BaseModel):
    task_id: str
    project_id: str
    title: str


class CreateApprovalInput(BaseModel):
    project_id: str
    task_id: str
    status: str = "pending"
    approved_by: str | None = None
    comment: str | None = None


class OrchestratorService:
    def __init__(self, registry: PlatformRegistry) -> None:
        self.registry = registry
        self.task_service = TaskService(registry.project_store, registry.task_store)
        self.decision_service = DecisionService(registry.decision_store)
        self.runtime = ProjectRuntime(registry)
        self.representative_workflow = RepresentativeWorkflow(
            runtime=self.runtime,
            task_service=self.task_service,
            decision_service=self.decision_service,
            approval_store=registry.approval_store,
        )

    def list_projects(self):
        return self.registry.project_store.list_projects()

    def get_project(self, project_id: str):
        return self.registry.project_store.get_project(project_id)

    def list_tasks(self, project_id: str | None = None) -> list[Task]:
        if project_id is not None:
            return self.registry.task_store.list_tasks(project_id)

        tasks: list[Task] = []
        for project in self.registry.project_store.list_projects():
            tasks.extend(self.registry.task_store.list_tasks(project.project_id))
        return tasks

    def create_task(self, project_id: str, user_input: str) -> CreateTaskResult:
        task = self.task_service.create_task(project_id=project_id, user_input=user_input)
        return CreateTaskResult(task_id=task.task_id, project_id=task.project_id, title=task.title)

    async def handle_user_control_message(self, project_id: str, user_input: str) -> TaskRunResult:
        created = self.create_task(project_id=project_id, user_input=user_input)
        project = self.runtime.get_project(project_id)
        chat_adapter = self.runtime.get_chat_adapter(project)
        initial_delivery = await chat_adapter.post_user_message(
            project,
            f"Representative received your request and created task {created.task_id}: {created.title}",
        )
        result = await self.run_task(created.task_id)
        result.chat_deliveries.insert(0, initial_delivery)
        return result

    async def run_task(self, task_id: str) -> TaskRunResult:
        task = self.task_service.get_task(task_id)
        if task is None:
            raise ValueError(f"Task '{task_id}' was not found.")

        try:
            return await self.representative_workflow.run(task)
        except Exception as exc:
            self.task_service.transition_task(
                task,
                stage=TaskStage.FAILED,
                status=TaskStatus.FAILED,
                summary=f"Task failed: {exc}",
            )
            raise ValueError(f"Task '{task.task_id}' failed during orchestration.") from exc

    def get_task_status(self, task_id: str) -> TaskStatusView | None:
        return self.task_service.get_task_status(task_id)

    def update_task_status(self, task_id: str, status: TaskStatus) -> Task | None:
        task = self.task_service.get_task(task_id)
        if task is None:
            return None
        return self.task_service.transition_task(task, stage=task.stage, status=status)

    def list_decisions(self, project_id: str | None = None):
        if project_id is None:
            decisions: list[Decision] = []
            for project in self.registry.project_store.list_projects():
                decisions.extend(self.registry.decision_store.list_decisions(project.project_id))
            return decisions
        return self.registry.decision_store.list_decisions(project_id)

    def record_decision(self, decision: Decision) -> Decision:
        return self.decision_service.record(decision)

    def list_approvals(self, project_id: str | None = None):
        if project_id is None:
            approvals: list[Approval] = []
            for project in self.registry.project_store.list_projects():
                approvals.extend(self.registry.approval_store.list_approvals(project.project_id))
            return approvals
        return self.registry.approval_store.list_approvals(project_id)

    def create_approval(self, payload: CreateApprovalInput) -> Approval:
        approval = Approval(
            task_id=payload.task_id,
            project_id=payload.project_id,
            approved_by=payload.approved_by,
            comment=payload.comment,
        )
        return self.registry.approval_store.upsert_approval(approval)

    async def approve_approval(
        self,
        approval_id: str,
        approved_by: str,
        comment: str | None = None,
        resume_task: bool = True,
    ) -> dict[str, object] | None:
        approval = self._get_approval_by_id(approval_id)
        if approval is None:
            return None

        updated_approval = approval.model_copy(
            update={
                "status": ApprovalStatus.APPROVED,
                "approved_by": approved_by,
                "comment": comment,
            }
        )
        self.registry.approval_store.upsert_approval(updated_approval)

        task = self.task_service.get_task(updated_approval.task_id)
        if task is None:
            raise ValueError(f"Task '{updated_approval.task_id}' was not found for approval '{approval_id}'.")

        resumed = False
        if resume_task and task.stage == TaskStage.WAITING_HUMAN:
            resumed = True
            task = await self.representative_workflow.resume_from_checkpoint(task, updated_approval)
        else:
            task = self.task_service.transition_task(
                task,
                stage=task.stage,
                status=task.status,
                summary=task.metadata.get("status_summary") if isinstance(task.metadata.get("status_summary"), str) else None,
            )

        return {"approval": updated_approval, "task": task, "resumed": resumed}

    def reject_approval(
        self,
        approval_id: str,
        approved_by: str,
        comment: str | None = None,
    ) -> dict[str, object] | None:
        approval = self._get_approval_by_id(approval_id)
        if approval is None:
            return None

        updated_approval = approval.model_copy(
            update={
                "status": ApprovalStatus.REJECTED,
                "approved_by": approved_by,
                "comment": comment,
            }
        )
        self.registry.approval_store.upsert_approval(updated_approval)

        task = self.task_service.get_task(updated_approval.task_id)
        if task is None:
            raise ValueError(f"Task '{updated_approval.task_id}' was not found for approval '{approval_id}'.")

        updated_task = self.task_service.transition_task(
            task,
            stage=TaskStage.FAILED,
            status=TaskStatus.FAILED,
            summary=f"Approval '{approval_id}' was rejected.",
        )
        return {"approval": updated_approval, "task": updated_task}

    def list_conversations(self, project_id: str | None = None):
        tasks = self.list_tasks(project_id)
        decisions_by_task: dict[tuple[str, str], Decision] = {}
        approvals_by_task: dict[tuple[str, str], list[Approval]] = {}

        for task_item in tasks:
            key = (task_item.project_id, task_item.task_id)
            decisions = self.registry.decision_store.list_decisions(task_item.project_id, task_item.task_id)
            if decisions:
                decisions_by_task[key] = sorted(decisions, key=lambda item: item.created_at, reverse=True)[0]
            approvals_by_task[key] = self.registry.approval_store.list_approvals(task_item.project_id, task_item.task_id)

        conversations: list[ConversationThread] = []
        for task_item in tasks:
            key = (task_item.project_id, task_item.task_id)
            run_metadata = task_item.metadata.get("run")
            if not isinstance(run_metadata, dict):
                continue

            messages: list[ConversationMessage] = []
            task_description = task_item.description.strip() if isinstance(task_item.description, str) else ""
            if task_description:
                messages.append(
                    ConversationMessage(
                        project_id=task_item.project_id,
                        domain=ConversationDomain.USER_CONTROL,
                        role="user",
                        content=task_description,
                    )
                )

            role_results = run_metadata.get("role_results")
            if isinstance(role_results, list):
                for role_result in role_results:
                    if not isinstance(role_result, dict):
                        continue
                    role = role_result.get("role")
                    output = role_result.get("output")
                    if isinstance(role, str) and isinstance(output, str):
                        messages.append(
                            ConversationMessage(
                                project_id=task_item.project_id,
                                domain=ConversationDomain.AI_OPS,
                                role=role,
                                content=output,
                                metadata={
                                    "provider": role_result.get("provider"),
                                    "model": role_result.get("model"),
                                },
                            )
                        )

            chat_deliveries = run_metadata.get("chat_deliveries")
            if isinstance(chat_deliveries, list):
                for delivery in chat_deliveries:
                    if not isinstance(delivery, dict):
                        continue
                    logical_channel = delivery.get("logical_channel")
                    if not isinstance(logical_channel, str):
                        continue
                    try:
                        domain = ConversationDomain(logical_channel)
                    except ValueError:
                        continue
                    messages.append(
                        ConversationMessage(
                            project_id=task_item.project_id,
                            domain=domain,
                            role="chat_delivery",
                            content=f"Delivered message to {delivery.get('platform')}:{delivery.get('physical_channel_id')}",
                            envelope=MessageEnvelope(
                                platform=str(delivery.get("platform")),
                                channel_id=str(delivery.get("physical_channel_id")),
                                thread_id=delivery.get("thread_id")
                                if isinstance(delivery.get("thread_id"), str)
                                else None,
                                message_id=delivery.get("message_id")
                                if isinstance(delivery.get("message_id"), str)
                                else None,
                            ),
                            metadata=delivery.get("metadata")
                            if isinstance(delivery.get("metadata"), dict)
                            else {},
                        )
                    )

            decision = decisions_by_task.get(key)
            if decision is not None:
                messages.append(
                    ConversationMessage(
                        project_id=task_item.project_id,
                        domain=ConversationDomain.AI_COUNCIL,
                        role="decision",
                        content=decision.summary,
                        metadata={
                            "decision_id": decision.decision_id,
                            "chosen_option": decision.chosen_option,
                        },
                    )
                )

            approvals = approvals_by_task.get(key, [])
            for approval in approvals:
                messages.append(
                    ConversationMessage(
                        project_id=task_item.project_id,
                        domain=ConversationDomain.USER_CONTROL,
                        role="approval",
                        content=approval.comment or f"Approval status changed to {approval.status.value}.",
                        metadata={
                            "approval_id": approval.approval_id,
                            "status": approval.status.value,
                            "approved_by": approval.approved_by,
                        },
                    )
                )

            if not messages:
                continue

            conversations.append(
                ConversationThread(
                    project_id=task_item.project_id,
                    task_id=task_item.task_id,
                    domain=ConversationDomain.AI_OPS,
                    title=task_item.title,
                    summary=task_item.metadata.get("status_summary")
                    if isinstance(task_item.metadata.get("status_summary"), str)
                    else None,
                    messages=messages,
                    created_at=task_item.created_at,
                    updated_at=task_item.updated_at,
                )
            )

        return sorted(conversations, key=lambda item: item.created_at, reverse=True)

    def _get_approval_by_id(self, approval_id: str) -> Approval | None:
        for project in self.registry.project_store.list_projects():
            approval = self.registry.approval_store.get_approval(project.project_id, approval_id)
            if approval is not None:
                return approval
        return None
