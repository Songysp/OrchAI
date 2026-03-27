from __future__ import annotations

from pydantic import Field

from packages.domain.models.common import (
    PlatformBaseModel,
    utc_now,
)


class Project(PlatformBaseModel):
    project_id: str
    repo_url: str
    workspace_path: str
    chat_platform: str
    default_branch: str = "main"
    created_at: datetime = Field(default_factory=utc_now)
    name: str | None = None
    description: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)
