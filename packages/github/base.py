from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field

from packages.domain.models import Project


class RepositoryContext(BaseModel):
    project: Project
    branch: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class PullRequestSummary(BaseModel):
    number: int | None = None
    title: str
    url: str | None = None
    status: str = "unknown"
    metadata: dict[str, Any] = Field(default_factory=dict)


class GitHubAdapter(ABC):
    @abstractmethod
    async def open_pull_request(self, context: RepositoryContext, title: str, body: str) -> PullRequestSummary:
        raise NotImplementedError
