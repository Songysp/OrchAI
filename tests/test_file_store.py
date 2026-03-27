from pathlib import Path

from packages.domain.models import Approval, ApprovalStatus, Decision, Project, Task, TaskStage, TaskStatus
from packages.storage.file_store import (
    FileApprovalStore,
    FileDecisionStore,
    FileProjectStore,
    FileTaskStore,
)


def test_file_stores_use_project_scoped_paths(tmp_path: Path) -> None:
    project_store = FileProjectStore(tmp_path)
    task_store = FileTaskStore(tmp_path)
    decision_store = FileDecisionStore(tmp_path)
    approval_store = FileApprovalStore(tmp_path)

    project = Project(
        project_id="project-alpha",
        repo_url="https://github.com/example/project-alpha",
        workspace_path="workspaces/project-alpha",
        chat_platform="slack",
        default_branch="main",
    )
    task = Task(
        task_id="task-001",
        project_id=project.project_id,
        title="Set up representative workflow",
        status=TaskStatus.PENDING,
        stage=TaskStage.PLANNING,
    )
    decision = Decision(
        decision_id="decision-001",
        task_id=task.task_id,
        project_id=project.project_id,
        summary="Use adapter-driven chat integrations.",
        chosen_option="adapter-driven-transport",
    )
    approval = Approval(
        approval_id="approval-001",
        task_id=task.task_id,
        project_id=project.project_id,
        status=ApprovalStatus.PENDING,
        approved_by=None,
        comment="Awaiting user approval.",
    )

    project_store.upsert_project(project)
    task_store.upsert_task(task)
    decision_store.upsert_decision(decision)
    approval_store.upsert_approval(approval)

    assert project_store.get_project(project.project_id) == project
    assert task_store.get_task(project.project_id, task.task_id) == task
    assert decision_store.get_decision(project.project_id, decision.decision_id) == decision
    assert approval_store.get_approval(project.project_id, approval.approval_id) == approval

    assert (tmp_path / "projects" / project.project_id / "project.json").exists()
    assert (tmp_path / "projects" / project.project_id / "tasks" / f"{task.task_id}.json").exists()
    assert (tmp_path / "projects" / project.project_id / "decisions" / f"{decision.decision_id}.json").exists()
    assert (tmp_path / "projects" / project.project_id / "approvals" / f"{approval.approval_id}.json").exists()
