from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field

from packages.domain.models import ExecutionBackend, Project, Task


class ExecutionRequest(BaseModel):
    project: Project
    task: Task
    command: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExecutionResult(BaseModel):
    backend: ExecutionBackend
    status: str
    summary: str
    logs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExecutionAdapter(ABC):
    backend_name: ExecutionBackend

    @abstractmethod
    async def run(self, request: ExecutionRequest) -> ExecutionResult:
        raise NotImplementedError
