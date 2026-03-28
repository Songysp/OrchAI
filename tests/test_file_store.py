from pathlib import Path

from packages.domain.models import (
    Approval,
    ApprovalStatus,
    Decision,
    ExecutionArtifact,
    ExecutionBackend,
    ExecutionRun,
    Project,
    Task,
    TaskStage,
    TaskStatus,
)
from packages.storage.file_store import (
    FileApprovalStore,
    FileDecisionStore,
    FileExecutionArtifactStore,
    FileExecutionRunStore,
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


def test_execution_run_and_artifact_stores_persist_content(tmp_path: Path) -> None:
    run_store = FileExecutionRunStore(tmp_path)
    artifact_store = FileExecutionArtifactStore(tmp_path)

    run = ExecutionRun(
        execution_id="run-001",
        project_id="project-alpha",
        task_id="task-001",
        backend=ExecutionBackend.CLI,
        command="pytest",
        status="completed",
        summary="Execution completed",
        logs=["stdout line", "stderr line"],
    )
    persisted_run = run_store.upsert_execution_run(run)
    assert run_store.get_execution_run("project-alpha", "run-001") == persisted_run

    artifact = ExecutionArtifact(
        artifact_id="artifact-001",
        execution_id=run.execution_id,
        project_id=run.project_id,
        task_id=run.task_id,
        name="stdout.txt",
        relative_path="",
        size_bytes=0,
        content_type="text/plain",
    )
    persisted_artifact = artifact_store.create_execution_artifact(artifact, b"hello artifact")

    assert artifact_store.get_execution_artifact("project-alpha", "artifact-001") == persisted_artifact
    assert artifact_store.read_execution_artifact("project-alpha", "artifact-001") == b"hello artifact"
    assert persisted_artifact.relative_path.startswith("execution_artifacts/files/run-001/")
