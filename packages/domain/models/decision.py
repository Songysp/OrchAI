from __future__ import annotations

from pydantic import Field

from packages.domain.models.common import PlatformBaseModel, new_id, utc_now


class Decision(PlatformBaseModel):
    decision_id: str = Field(default_factory=new_id)
    task_id: str
    project_id: str
    summary: str
    chosen_option: str
    created_at: datetime = Field(default_factory=utc_now)
