from __future__ import annotations

import json
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import TypeVar

from pydantic import BaseModel

from packages.domain.models import Approval, Decision, ExecutionArtifact, ExecutionRun, Project, Task
from packages.storage.base import (
    ApprovalStore,
    DecisionStore,
    ExecutionArtifactStore,
    ExecutionRunStore,
    ProjectStore,
    TaskStore,
)


ModelT = TypeVar("ModelT", bound=BaseModel)


class FileStoreBase:
    def __init__(self, root_path: Path) -> None:
        self.root_path = root_path
        self.projects_root = self.root_path / "projects"
        self.projects_root.mkdir(parents=True, exist_ok=True)

    def _project_dir(self, project_id: str) -> Path:
        path = self.projects_root / project_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _write_json_atomic(self, path: Path, payload: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile("w", encoding="utf-8", delete=False, dir=path.parent, suffix=".tmp") as handle:
            json.dump(payload, handle, indent=2)
            temp_path = Path(handle.name)
        temp_path.replace(path)

    def _read_model(self, path: Path, model_type: type[ModelT]) -> ModelT | None:
        if not path.exists():
            return None
        payload = json.loads(path.read_text(encoding="utf-8"))
        return model_type.model_validate(payload)

    def _read_models(self, directory: Path, model_type: type[ModelT]) -> list[ModelT]:
        if not directory.exists():
            return []
        items: list[ModelT] = []
        for path in sorted(directory.glob("*.json")):
            item = self._read_model(path, model_type)
            if item is not None:
                items.append(item)
        return items


class FileProjectStore(FileStoreBase, ProjectStore):
    def list_projects(self) -> list[Project]:
        projects: list[Project] = []
        for project_dir in sorted(self.projects_root.iterdir()):
            if not project_dir.is_dir():
                continue
            project = self.get_project(project_dir.name)
            if project is not None:
                projects.append(project)
        return projects

    def get_project(self, project_id: str) -> Project | None:
        return self._read_model(self._project_dir(project_id) / "project.json", Project)

    def upsert_project(self, project: Project) -> Project:
        self._write_json_atomic(
            self._project_dir(project.project_id) / "project.json",
            project.model_dump(mode="json"),
        )
        return project


class FileTaskStore(FileStoreBase, TaskStore):
    def _tasks_dir(self, project_id: str) -> Path:
        path = self._project_dir(project_id) / "tasks"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def list_tasks(self, project_id: str) -> list[Task]:
        return self._read_models(self._tasks_dir(project_id), Task)

    def get_task(self, project_id: str, task_id: str) -> Task | None:
        return self._read_model(self._tasks_dir(project_id) / f"{task_id}.json", Task)

    def upsert_task(self, task: Task) -> Task:
        self._write_json_atomic(
            self._tasks_dir(task.project_id) / f"{task.task_id}.json",
            task.model_dump(mode="json"),
        )
        return task


class FileDecisionStore(FileStoreBase, DecisionStore):
    def _decisions_dir(self, project_id: str) -> Path:
        path = self._project_dir(project_id) / "decisions"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def list_decisions(self, project_id: str, task_id: str | None = None) -> list[Decision]:
        decisions = self._read_models(self._decisions_dir(project_id), Decision)
        if task_id is None:
            return decisions
        return [decision for decision in decisions if decision.task_id == task_id]

    def get_decision(self, project_id: str, decision_id: str) -> Decision | None:
        return self._read_model(self._decisions_dir(project_id) / f"{decision_id}.json", Decision)

    def upsert_decision(self, decision: Decision) -> Decision:
        self._write_json_atomic(
            self._decisions_dir(decision.project_id) / f"{decision.decision_id}.json",
            decision.model_dump(mode="json"),
        )
        return decision


class FileApprovalStore(FileStoreBase, ApprovalStore):
    def _approvals_dir(self, project_id: str) -> Path:
        path = self._project_dir(project_id) / "approvals"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def list_approvals(self, project_id: str, task_id: str | None = None) -> list[Approval]:
        approvals = self._read_models(self._approvals_dir(project_id), Approval)
        if task_id is None:
            return approvals
        return [approval for approval in approvals if approval.task_id == task_id]

    def get_approval(self, project_id: str, approval_id: str) -> Approval | None:
        return self._read_model(self._approvals_dir(project_id) / f"{approval_id}.json", Approval)

    def upsert_approval(self, approval: Approval) -> Approval:
        self._write_json_atomic(
            self._approvals_dir(approval.project_id) / f"{approval.approval_id}.json",
            approval.model_dump(mode="json"),
        )
        return approval


class FileExecutionRunStore(FileStoreBase, ExecutionRunStore):
    def _execution_runs_dir(self, project_id: str) -> Path:
        path = self._project_dir(project_id) / "execution_runs"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def list_execution_runs(self, project_id: str, task_id: str | None = None) -> list[ExecutionRun]:
        runs = self._read_models(self._execution_runs_dir(project_id), ExecutionRun)
        if task_id is None:
            return runs
        return [run for run in runs if run.task_id == task_id]

    def get_execution_run(self, project_id: str, execution_id: str) -> ExecutionRun | None:
        return self._read_model(self._execution_runs_dir(project_id) / f"{execution_id}.json", ExecutionRun)

    def upsert_execution_run(self, run: ExecutionRun) -> ExecutionRun:
        self._write_json_atomic(
            self._execution_runs_dir(run.project_id) / f"{run.execution_id}.json",
            run.model_dump(mode="json"),
        )
        return run


class FileExecutionArtifactStore(FileStoreBase, ExecutionArtifactStore):
    def _artifacts_dir(self, project_id: str) -> Path:
        path = self._project_dir(project_id) / "execution_artifacts"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _artifact_index_dir(self, project_id: str) -> Path:
        path = self._artifacts_dir(project_id) / "index"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _artifact_files_dir(self, project_id: str) -> Path:
        path = self._artifacts_dir(project_id) / "files"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _safe_filename(self, value: str) -> str:
        return "".join(char if char.isalnum() or char in {"-", "_", "."} else "-" for char in value)[:120]

    def _artifact_content_path(self, artifact: ExecutionArtifact) -> Path:
        return self._project_dir(artifact.project_id) / artifact.relative_path

    def list_execution_artifacts(
        self,
        project_id: str,
        execution_id: str | None = None,
        task_id: str | None = None,
    ) -> list[ExecutionArtifact]:
        artifacts = self._read_models(self._artifact_index_dir(project_id), ExecutionArtifact)
        if execution_id is not None:
            artifacts = [item for item in artifacts if item.execution_id == execution_id]
        if task_id is not None:
            artifacts = [item for item in artifacts if item.task_id == task_id]
        return artifacts

    def get_execution_artifact(self, project_id: str, artifact_id: str) -> ExecutionArtifact | None:
        return self._read_model(self._artifact_index_dir(project_id) / f"{artifact_id}.json", ExecutionArtifact)

    def create_execution_artifact(self, artifact: ExecutionArtifact, content: bytes) -> ExecutionArtifact:
        safe_name = self._safe_filename(artifact.name)
        content_path = (
            self._artifact_files_dir(artifact.project_id)
            / artifact.execution_id
            / f"{artifact.artifact_id}-{safe_name}"
        )
        content_path.parent.mkdir(parents=True, exist_ok=True)
        content_path.write_bytes(content)
        relative_path = content_path.relative_to(self._project_dir(artifact.project_id)).as_posix()
        updated = artifact.model_copy(
            update={
                "relative_path": relative_path,
                "size_bytes": len(content),
            }
        )
        self._write_json_atomic(
            self._artifact_index_dir(updated.project_id) / f"{updated.artifact_id}.json",
            updated.model_dump(mode="json"),
        )
        return updated

    def read_execution_artifact(self, project_id: str, artifact_id: str) -> bytes | None:
        artifact = self.get_execution_artifact(project_id, artifact_id)
        if artifact is None:
            return None
        content_path = self._artifact_content_path(artifact)
        if not content_path.exists():
            return None
        return content_path.read_bytes()
