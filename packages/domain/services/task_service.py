from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from packages.domain.models import Task, TaskStage, TaskStatus
from packages.domain.models.common import utc_now
from packages.storage.base import ProjectStore, TaskStore


class TaskStatusView(BaseModel):
    task_id: str
    project_id: str
    status: TaskStatus
    stage: TaskStage
    updated_at: datetime
    summary: str | None = None


class TaskService:
    def __init__(self, project_store: ProjectStore, task_store: TaskStore) -> None:
        self.project_store = project_store
        self.task_store = task_store

    def create_task(self, project_id: str, user_input: str) -> Task:
        project = self.project_store.get_project(project_id)
        if project is None:
            raise ValueError(f"Project '{project_id}' was not found.")

        task = Task(
            project_id=project.project_id,
            title=self._derive_title(user_input),
            description=user_input,
            created_by="user",
            status=TaskStatus.PENDING,
            stage=TaskStage.CREATED,
            metadata={"user_input": user_input},
        )
        return self.task_store.upsert_task(task)

    def get_task(self, task_id: str) -> Task | None:
        for project in self.project_store.list_projects():
            task = self.task_store.get_task(project.project_id, task_id)
            if task is not None:
                return task
        return None

    def transition_task(self, task: Task, stage: TaskStage, status: TaskStatus, summary: str | None = None) -> Task:
        metadata = dict(task.metadata)
        if summary is not None:
            metadata["status_summary"] = summary
        updated = task.model_copy(
            update={
                "stage": stage,
                "status": status,
                "updated_at": utc_now(),
                "metadata": metadata,
            }
        )
        return self.task_store.upsert_task(updated)

    def get_task_status(self, task_id: str) -> TaskStatusView | None:
        task = self.get_task(task_id)
        if task is None:
            return None
        return TaskStatusView(
            task_id=task.task_id,
            project_id=task.project_id,
            status=task.status,
            stage=task.stage,
            updated_at=task.updated_at,
            summary=self._summary_from(task),
        )

    def _derive_title(self, user_input: str) -> str:
        compact = " ".join(user_input.split())
        return compact[:80] if compact else "New orchestration task"

    def _summary_from(self, task: Task) -> str | None:
        summary = task.metadata.get("status_summary")
        return summary if isinstance(summary, str) else None
