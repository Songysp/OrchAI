from __future__ import annotations

from datetime import datetime

from pydantic import Field
from pydantic import model_validator

from packages.domain.models.common import (
    ConversationDomain,
    PlatformBaseModel,
    utc_now,
)


class ChannelBinding(PlatformBaseModel):
    domain: ConversationDomain
    channel_id: str
    thread_enabled: bool = True
    metadata: dict[str, object] = Field(default_factory=dict)


class AgentMapping(PlatformBaseModel):
    role: str
    provider: str
    model: str | None = None
    metadata: dict[str, object] = Field(default_factory=dict)


class Project(PlatformBaseModel):
    project_id: str
    repo_url: str
    workspace_path: str
    chat_platform: str
    default_branch: str = "main"
    created_at: datetime = Field(default_factory=utc_now)
    name: str | None = None
    description: str | None = None
    channel_bindings: dict[str, ChannelBinding] = Field(default_factory=dict)
    agent_mapping: dict[str, AgentMapping] = Field(default_factory=dict)
    execution_backend: str | None = None
    commands: dict[str, object] = Field(default_factory=dict)
    rules: list[dict[str, object]] = Field(default_factory=list)
    metadata: dict[str, object] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def hydrate_repo_fields(cls, data: object) -> object:
        if not isinstance(data, dict):
            return data

        repo = data.get("repo")
        if isinstance(repo, dict):
            data.setdefault("repo_url", repo.get("url"))
            data.setdefault("default_branch", repo.get("default_branch", "main"))
            data.pop("repo", None)
        return data
