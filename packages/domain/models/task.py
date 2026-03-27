from __future__ import annotations

from typing import Any

from pydantic import Field

from packages.domain.models.common import AuditRecord, PlatformBaseModel, TaskStatus, new_id


class TaskArtifact(PlatformBaseModel):
    name: str
    kind: str
    uri: str | None = None
    content: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class TaskEvent(PlatformBaseModel):
    event_id: str = Field(default_factory=new_id)
    task_id: str
    event_type: str
    actor: str
    summary: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class Task(AuditRecord):
    task_id: str = Field(default_factory=new_id)
    project_id: str
    title: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    created_by: str = "user"
    assigned_roles: list[str] = Field(default_factory=list)
    artifacts: list[TaskArtifact] = Field(default_factory=list)
    labels: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
