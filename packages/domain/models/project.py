from __future__ import annotations

from typing import Any

from pydantic import Field

from packages.domain.models.common import (
    AuditRecord,
    ConversationDomain,
    ExecutionBackend,
    PlatformBaseModel,
    ProjectStatus,
)


class RepoMetadata(PlatformBaseModel):
    url: str
    default_branch: str = "main"
    provider: str = "github"


class ChannelBinding(PlatformBaseModel):
    domain: ConversationDomain
    channel_id: str
    thread_enabled: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentRoleConfig(PlatformBaseModel):
    role: str
    provider: str
    model: str | None = None
    system_prompt: str | None = None
    options: dict[str, Any] = Field(default_factory=dict)


class CommandSet(PlatformBaseModel):
    plan: str | None = None
    build: str | None = None
    test: str | None = None
    lint: str | None = None
    fix: str | None = None
    setup: str | None = None


class PolicyRule(PlatformBaseModel):
    rule_id: str
    condition: str
    action: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class Project(PlatformBaseModel):
    project_id: str
    name: str
    description: str | None = None
    status: ProjectStatus = ProjectStatus.ACTIVE
    chat_platform: str
    repo: RepoMetadata
    workspace_path: str
    execution_backend: ExecutionBackend = ExecutionBackend.CLI
    channel_bindings: dict[ConversationDomain, ChannelBinding]
    agent_mapping: dict[str, AgentRoleConfig]
    commands: CommandSet = Field(default_factory=CommandSet)
    rules: list[PolicyRule] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ProjectSummary(AuditRecord):
    project: Project
