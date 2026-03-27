from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field

from packages.domain.models import PolicyRule, Project, Task


class RuleEvaluation(BaseModel):
    allowed: bool
    triggered_rules: list[str] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class RulesEngine(ABC):
    @abstractmethod
    def evaluate_task(self, project: Project, task: Task) -> RuleEvaluation:
        raise NotImplementedError

    @abstractmethod
    def evaluate_rules(self, project: Project, rules: list[PolicyRule], context: dict[str, Any]) -> RuleEvaluation:
        raise NotImplementedError
