from __future__ import annotations

from typing import Any

from pydantic import Field

from packages.domain.models.common import ApprovalStatus, AuditRecord, new_id


class ApprovalRequest(AuditRecord):
    approval_id: str = Field(default_factory=new_id)
    project_id: str
    task_id: str | None = None
    requested_by: str
    reason: str
    status: ApprovalStatus = ApprovalStatus.PENDING
    context: dict[str, Any] = Field(default_factory=dict)
    resolution_note: str | None = None
