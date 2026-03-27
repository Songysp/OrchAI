from __future__ import annotations

from pydantic import Field

from packages.domain.models.common import AuditRecord, TaskStage, TaskStatus, new_id


class Task(AuditRecord):
    task_id: str = Field(default_factory=new_id)
    project_id: str
    title: str
    status: TaskStatus = TaskStatus.PENDING
    stage: TaskStage = TaskStage.CREATED
    description: str | None = None
    created_by: str | None = None
    metadata: dict[str, object] = Field(default_factory=dict)
