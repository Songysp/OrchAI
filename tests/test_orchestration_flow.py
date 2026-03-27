from pathlib import Path

import pytest

from apps.orchestrator.services.orchestrator_service import OrchestratorService
from packages.domain.models import TaskStage, TaskStatus
from packages.domain.services.registry import PlatformRegistry


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


@pytest.mark.anyio
async def test_representative_orchestration_flow_persists_task_and_decision(tmp_path: Path) -> None:
    _write_text(
        tmp_path / "configs" / "platform.yaml",
        "\n".join(
            [
                "app_name: AI Dev Team Platform",
                "api_host: 0.0.0.0",
                "api_port: 8000",
                "paths:",
                "  data_dir: data",
                "  projects_dir: configs/projects",
                "  workspaces_dir: workspaces",
            ]
        ),
    )
    _write_text(
        tmp_path / "configs" / "projects" / "sample.yaml",
        "\n".join(
            [
                "project_id: sample-project",
                "name: Sample Project",
                "repo_url: https://github.com/example/sample-project",
                "workspace_path: workspaces/sample-project",
                "chat_platform: slack",
                "default_branch: main",
                "channel_bindings:",
                "  ai-council:",
                "    domain: ai-council",
                "    channel_id: C_COUNCIL",
                "  ai-ops:",
                "    domain: ai-ops",
                "    channel_id: C_OPS",
                "  user-control:",
                "    domain: user-control",
                "    channel_id: C_USER",
                "agent_mapping:",
                "  representative:",
                "    role: representative",
                "    provider: claude",
                "    model: claude-sonnet",
                "  planner:",
                "    role: planner",
                "    provider: gemini",
                "    model: gemini-pro",
                "  builder:",
                "    role: builder",
                "    provider: codex",
                "    model: codex-latest",
                "  critic:",
                "    role: critic",
                "    provider: claude",
                "    model: claude-sonnet",
                "  tester:",
                "    role: tester",
                "    provider: gemini",
                "    model: gemini-pro",
            ]
        ),
    )

    service = OrchestratorService(PlatformRegistry(tmp_path))

    created = service.create_task("sample-project", "Build the first orchestration flow for the platform")
    status_before = service.get_task_status(created.task_id)
    assert status_before is not None
    assert status_before.stage == TaskStage.CREATED
    assert status_before.status == TaskStatus.PENDING

    result = await service.run_task(created.task_id)
    status_after = service.get_task_status(created.task_id)

    assert result.final_stage == TaskStage.COMPLETED
    assert result.final_status == TaskStatus.COMPLETED
    assert len(result.role_results) == 5
    assert status_after is not None
    assert status_after.stage == TaskStage.COMPLETED
    assert status_after.status == TaskStatus.COMPLETED

    decisions = service.list_decisions("sample-project")
    assert len(decisions) == 1
    assert decisions[0].task_id == created.task_id
    assert decisions[0].summary

    task_path = tmp_path / "data" / "projects" / "sample-project" / "tasks" / f"{created.task_id}.json"
    decision_path = tmp_path / "data" / "projects" / "sample-project" / "decisions" / f"{decisions[0].decision_id}.json"
    assert task_path.exists()
    assert decision_path.exists()


@pytest.mark.anyio
async def test_orchestration_flow_creates_approval_when_policy_matches(tmp_path: Path) -> None:
    _write_text(
        tmp_path / "configs" / "platform.yaml",
        "\n".join(
            [
                "app_name: AI Dev Team Platform",
                "api_host: 0.0.0.0",
                "api_port: 8000",
                "paths:",
                "  data_dir: data",
                "  projects_dir: configs/projects",
                "  workspaces_dir: workspaces",
            ]
        ),
    )
    _write_text(
        tmp_path / "configs" / "projects" / "policy-project.yaml",
        "\n".join(
            [
                "project_id: policy-project",
                "name: Policy Project",
                "repo_url: https://github.com/example/policy-project",
                "workspace_path: workspaces/policy-project",
                "chat_platform: slack",
                "default_branch: main",
                "agent_mapping:",
                "  representative:",
                "    role: representative",
                "    provider: claude",
                "  planner:",
                "    role: planner",
                "    provider: gemini",
                "  builder:",
                "    role: builder",
                "    provider: codex",
                "  critic:",
                "    role: critic",
                "    provider: claude",
                "  tester:",
                "    role: tester",
                "    provider: gemini",
                "rules:",
                "  - rule_id: require-auth-approval",
                "    action: require_approval",
                "    condition: auth",
                "  - rule_id: max-debate-rounds",
                "    action: set_limit",
                "    limit_key: max_debate_rounds",
                "    value: 3",
            ]
        ),
    )

    service = OrchestratorService(PlatformRegistry(tmp_path))
    created = service.create_task("policy-project", "Refactor auth pipeline for the representative workflow")
    result = await service.run_task(created.task_id)
    approvals = service.list_approvals("policy-project")
    status = service.get_task_status(created.task_id)

    assert result.approval_required is True
    assert result.approval_id is not None
    assert len(approvals) == 1
    assert status is not None
    assert status.stage == TaskStage.WAITING_HUMAN
    assert status.status == TaskStatus.BLOCKED
