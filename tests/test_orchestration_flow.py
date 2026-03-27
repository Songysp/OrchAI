from pathlib import Path

import pytest

from apps.orchestrator.services.orchestrator_service import OrchestratorService
from packages.domain.models import ApprovalStatus, ConversationDomain, TaskStage, TaskStatus
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
                "    parameters:",
                "      temperature: 0.2",
                "  planner:",
                "    role: planner",
                "    provider: gemini",
                "    model: gemini-pro",
                "    parameters:",
                "      temperature: 0.1",
                "  builder:",
                "    role: builder",
                "    provider: codex",
                "    model: codex-latest",
                "    parameters:",
                "      temperature: 0.0",
                "  critic:",
                "    role: critic",
                "    provider: claude",
                "    model: claude-sonnet",
                "    parameters:",
                "      temperature: 0.3",
                "  tester:",
                "    role: tester",
                "    provider: gemini",
                "    model: gemini-pro",
                "    parameters:",
                "      temperature: 0.1",
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
    builder_result = next(result for result in result.role_results if result.role == "builder")
    assert builder_result.provider == "codex"
    assert builder_result.model == "codex-latest"
    assert builder_result.metadata["parameters"]["temperature"] == 0.0
    routed_channels = {delivery.logical_channel for delivery in result.chat_deliveries}
    assert ConversationDomain.USER_CONTROL in routed_channels
    assert ConversationDomain.AI_COUNCIL in routed_channels
    assert ConversationDomain.AI_OPS in routed_channels
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
                "    parameters:",
                "      temperature: 0.2",
                "  planner:",
                "    role: planner",
                "    provider: gemini",
                "    parameters:",
                "      temperature: 0.1",
                "  builder:",
                "    role: builder",
                "    provider: codex",
                "    parameters:",
                "      temperature: 0.0",
                "  critic:",
                "    role: critic",
                "    provider: claude",
                "    parameters:",
                "      temperature: 0.3",
                "  tester:",
                "    role: tester",
                "    provider: gemini",
                "    parameters:",
                "      temperature: 0.1",
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
    assert any(delivery.logical_channel == ConversationDomain.USER_CONTROL for delivery in result.chat_deliveries)
    approval_delivery = next(
        delivery
        for delivery in result.chat_deliveries
        if delivery.logical_channel == ConversationDomain.USER_CONTROL
        and "Approval ID:" in str(delivery.metadata.get("content", ""))
    )
    approval_message = str(approval_delivery.metadata.get("content", ""))
    assert f"task {created.task_id}" in approval_message
    assert result.approval_id in approval_message
    assert "/approve " in approval_message
    assert "/reject " in approval_message
    assert "/status " in approval_message
    assert status is not None
    assert status.stage == TaskStage.WAITING_HUMAN
    assert status.status == TaskStatus.BLOCKED

    approval_id = result.approval_id
    assert approval_id is not None

    approval_result = await service.approve_approval(
        approval_id=approval_id,
        approved_by="tester",
        comment="Approved to continue",
        resume_task=True,
    )
    assert approval_result is not None
    assert approval_result["approval"].status == ApprovalStatus.APPROVED
    assert approval_result["resumed"] is True
    assert approval_result["task"].stage == TaskStage.COMPLETED
    assert approval_result["task"].status == TaskStatus.COMPLETED
    resumed_task = service.task_service.get_task(created.task_id)
    assert resumed_task is not None
    assert resumed_task.metadata["run"]["resumed_from_checkpoint"] is True
    assert resumed_task.metadata["run"]["resumed_approval_id"] == approval_id
    decisions_after_resume = service.list_decisions("policy-project")
    assert len(decisions_after_resume) == 1
