from packages.domain.models import Project, Task
from packages.rules import SimpleRulesEngine


def test_policy_evaluator_requires_approval_and_extracts_limits() -> None:
    project = Project(
        project_id="project-policy",
        repo_url="https://github.com/example/project-policy",
        workspace_path="workspaces/project-policy",
        chat_platform="slack",
        rules=[
            {"rule_id": "require-auth-approval", "action": "require_approval", "condition": "auth"},
            {"rule_id": "require-db-approval", "action": "require_approval", "condition": "schema"},
            {"rule_id": "max-debate-rounds", "action": "set_limit", "limit_key": "max_debate_rounds", "value": 3},
            {"rule_id": "retry-limit", "action": "set_limit", "limit_key": "retry_limit", "value": 2},
        ],
    )
    task = Task(
        project_id=project.project_id,
        title="Update auth flow",
        description="Change auth middleware and schema migration handling",
    )

    evaluation = SimpleRulesEngine().evaluate(
        project=project,
        task=task,
        context={"builder": "This touches auth and schema changes."},
    )

    assert evaluation.approval_required is True
    assert "require-auth-approval" in evaluation.triggered_rules
    assert "require-db-approval" in evaluation.triggered_rules
    assert evaluation.limits["max_debate_rounds"] == 3
    assert evaluation.limits["retry_limit"] == 2
