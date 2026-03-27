from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field

from packages.domain.models import Project, Task


class PolicyEvaluation(BaseModel):
    approval_required: bool = False
    triggered_rules: list[str] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)
    limits: dict[str, int] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class RulesEngine(ABC):
    @abstractmethod
    def evaluate(self, project: Project, task: Task, context: dict[str, Any]) -> PolicyEvaluation:
        raise NotImplementedError
