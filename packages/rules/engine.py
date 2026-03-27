from __future__ import annotations

from typing import Any

from packages.domain.models import Project, Task
from packages.rules.base import PolicyEvaluation, RulesEngine


class SimpleRulesEngine(RulesEngine):
    """Simple project-config-driven policy evaluator.

    Supported MVP rule shapes:
    - requires_approval rules:
      {"rule_id": "...", "action": "require_approval", "condition": "auth"}
    - limit rules:
      {"rule_id": "...", "action": "set_limit", "limit_key": "max_debate_rounds", "value": 3}
    """

    def evaluate(self, project: Project, task: Task, context: dict[str, Any]) -> PolicyEvaluation:
        combined_text = self._combined_text(task, context)
        triggered_rules: list[str] = []
        reasons: list[str] = []
        limits: dict[str, int] = {}
        approval_required = False

        for rule in project.rules:
            rule_id = str(rule.get("rule_id", "unnamed-rule"))
            action = str(rule.get("action", "")).lower()

            if action == "require_approval":
                condition = str(rule.get("condition", "")).lower()
                if condition and condition in combined_text:
                    approval_required = True
                    triggered_rules.append(rule_id)
                    reasons.append(f"Rule '{rule_id}' requires approval because condition '{condition}' matched.")

            if action == "set_limit":
                limit_key = rule.get("limit_key")
                value = rule.get("value")
                if isinstance(limit_key, str) and isinstance(value, int):
                    limits[limit_key] = value

        return PolicyEvaluation(
            approval_required=approval_required,
            triggered_rules=triggered_rules,
            reasons=reasons,
            limits=limits,
            metadata={"project_id": project.project_id, "task_id": task.task_id},
        )

    def _combined_text(self, task: Task, context: dict[str, Any]) -> str:
        parts = [task.title, task.description or ""]
        for value in context.values():
            if isinstance(value, str):
                parts.append(value)
            elif isinstance(value, list):
                parts.extend(str(item) for item in value)
            elif isinstance(value, dict):
                parts.extend(str(item) for item in value.values())
            else:
                parts.append(str(value))
        return " ".join(parts).lower()
