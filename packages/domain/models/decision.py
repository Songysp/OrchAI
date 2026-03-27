from __future__ import annotations

from typing import Any

from pydantic import Field

from packages.domain.models.common import AuditRecord, new_id


class Decision(AuditRecord):
    decision_id: str = Field(default_factory=new_id)
    project_id: str
    task_id: str | None = None
    title: str
    summary: str
    rationale: str
    made_by: str
    approved: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)
