from __future__ import annotations

from packages.domain.models import PolicyRule, Project, Task
from packages.rules.base import RuleEvaluation, RulesEngine


class SimpleRulesEngine(RulesEngine):
    def evaluate_task(self, project: Project, task: Task) -> RuleEvaluation:
        context = {
            "task_title": task.title.lower(),
            "task_description": task.description.lower(),
            "labels": [label.lower() for label in task.labels],
        }
        return self.evaluate_rules(project, project.rules, context)

    def evaluate_rules(self, project: Project, rules: list[PolicyRule], context: dict[str, object]) -> RuleEvaluation:
        triggered_rules: list[str] = []
        reasons: list[str] = []

        haystack = " ".join(str(value) for value in context.values()).lower()
        for rule in rules:
            condition = rule.condition.lower()
            if condition and condition in haystack:
                triggered_rules.append(rule.rule_id)
                reasons.append(f"Rule '{rule.rule_id}' matched condition '{rule.condition}'.")

        return RuleEvaluation(
            allowed=not triggered_rules,
            triggered_rules=triggered_rules,
            reasons=reasons,
            metadata={"project_id": project.project_id},
        )
