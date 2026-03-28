from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field

from packages.domain.models import Project


class AgentSelection(BaseModel):
    role: str
    provider: str
    model: str | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)


class AgentTurnRequest(BaseModel):
    project: Project
    role: str
    prompt: str
    agent_selection: AgentSelection
    context: dict[str, Any] = Field(default_factory=dict)


class AgentTurnResult(BaseModel):
    role: str
    provider: str
    model: str | None = None
    output: str
    status: str = "completed"
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentAdapter(ABC):
    provider_name: str

    @abstractmethod
    async def run_turn(self, request: AgentTurnRequest) -> AgentTurnResult:
        raise NotImplementedError
