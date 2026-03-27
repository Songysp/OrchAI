from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def new_id() -> str:
    return uuid4().hex


class PlatformBaseModel(BaseModel):
    model_config = {"extra": "forbid", "populate_by_name": True}


class StringEnum(str, Enum):
    """Python 3.10-compatible replacement for StrEnum."""


class ProjectStatus(StringEnum):
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class TaskStatus(StringEnum):
    PENDING = "pending"
    PLANNING = "planning"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    REVIEW = "review"
    TESTING = "testing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


class TaskStage(StringEnum):
    CREATED = "created"
    PLANNING = "planning"
    BUILDING = "building"
    REVIEWING = "reviewing"
    TESTING = "testing"
    WAITING_HUMAN = "waiting_human"
    COMPLETED = "completed"
    FAILED = "failed"


class ApprovalStatus(StringEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class ConversationDomain(StringEnum):
    AI_COUNCIL = "ai-council"
    AI_OPS = "ai-ops"
    USER_CONTROL = "user-control"


class ExecutionBackend(StringEnum):
    CLI = "cli"
    GITHUB_ACTIONS = "github_actions"


class ProviderKind(StringEnum):
    CLAUDE = "claude"
    GEMINI = "gemini"
    CODEX = "codex"
    CUSTOM = "custom"


class AuditRecord(PlatformBaseModel):
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
