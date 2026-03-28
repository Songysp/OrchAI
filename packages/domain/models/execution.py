from __future__ import annotations

from datetime import datetime

from pydantic import Field

from packages.domain.models.common import AuditRecord, ExecutionBackend, new_id, utc_now


class ExecutionRun(AuditRecord):
    execution_id: str = Field(default_factory=new_id)
    project_id: str
    task_id: str
    backend: ExecutionBackend
    command: str
    status: str
    summary: str
    started_at: datetime = Field(default_factory=utc_now)
    finished_at: datetime | None = None
    logs: list[str] = Field(default_factory=list)
    artifact_ids: list[str] = Field(default_factory=list)
    metadata: dict[str, object] = Field(default_factory=dict)


class ExecutionArtifact(AuditRecord):
    artifact_id: str = Field(default_factory=new_id)
    execution_id: str
    project_id: str
    task_id: str
    name: str
    relative_path: str
    size_bytes: int
    content_type: str = "text/plain; charset=utf-8"
    metadata: dict[str, object] = Field(default_factory=dict)
