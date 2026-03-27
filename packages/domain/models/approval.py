from __future__ import annotations

from pydantic import Field

from packages.domain.models.common import ApprovalStatus, PlatformBaseModel, new_id, utc_now


class Approval(PlatformBaseModel):
    approval_id: str = Field(default_factory=new_id)
    task_id: str
    project_id: str
    status: ApprovalStatus = ApprovalStatus.PENDING
    approved_by: str | None = None
    comment: str | None = None
    created_at: datetime = Field(default_factory=utc_now)
