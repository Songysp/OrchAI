from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field

from packages.domain.models import (
    ApprovalRequest,
    ApprovalStatus,
    ConversationDomain,
    ConversationMessage,
    ConversationThread,
    Decision,
    Task,
    TaskStatus,
)
from packages.domain.services.registry import PlatformRegistry


class CreateTaskInput(BaseModel):
    project_id: str
    title: str
    description: str
    created_by: str = "user"
    labels: list[str] = Field(default_factory=list)


class CreateApprovalInput(BaseModel):
    project_id: str
    task_id: str | None = None
    requested_by: str
    reason: str
    context: dict[str, object] = Field(default_factory=dict)


class OrchestratorService:
    def __init__(self, registry: PlatformRegistry) -> None:
        self.registry = registry

    def list_projects(self):
        return self.registry.project_store.list_projects()

    def get_project(self, project_id: str):
        return self.registry.project_store.get_project(project_id)

    def list_tasks(self, project_id: str | None = None):
        return self.registry.task_store.list_tasks(project_id)

    def create_task(self, payload: CreateTaskInput) -> Task:
        task = Task(
            project_id=payload.project_id,
            title=payload.title,
            description=payload.description,
            created_by=payload.created_by,
            labels=payload.labels,
            status=TaskStatus.PENDING,
        )
        self.registry.task_store.upsert_task(task)

        conversation = ConversationThread(
            project_id=payload.project_id,
            domain=ConversationDomain.AI_OPS,
            title=f"Task {task.task_id}: {task.title}",
            messages=[
                ConversationMessage(
                    project_id=payload.project_id,
                    domain=ConversationDomain.AI_OPS,
                    role="system",
                    content=f"Task created with status '{task.status}'.",
                )
            ],
        )
        self.registry.conversation_store.upsert_conversation(conversation)
        return task

    def update_task_status(self, task_id: str, status: TaskStatus) -> Task | None:
        task = self.registry.task_store.get_task(task_id)
        if task is None:
            return None
        now = datetime.now(timezone.utc)
        updated = task.model_copy(update={"status": status, "updated_at": now})
        self.registry.task_store.upsert_task(updated)
        return updated

    def list_approvals(self, project_id: str | None = None):
        return self.registry.approval_store.list_approvals(project_id)

    def create_approval(self, payload: CreateApprovalInput) -> ApprovalRequest:
        approval = ApprovalRequest(
            project_id=payload.project_id,
            task_id=payload.task_id,
            requested_by=payload.requested_by,
            reason=payload.reason,
            context=payload.context,
            status=ApprovalStatus.PENDING,
        )
        self.registry.approval_store.upsert_approval(approval)
        return approval

    def list_decisions(self, project_id: str | None = None):
        return self.registry.decision_store.list_decisions(project_id)

    def record_decision(self, decision: Decision) -> Decision:
        return self.registry.decision_store.upsert_decision(decision)

    def list_conversations(self, project_id: str | None = None):
        return self.registry.conversation_store.list_conversations(project_id)
