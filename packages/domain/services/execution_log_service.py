from __future__ import annotations

from typing import Iterable

from packages.domain.models import ExecutionArtifact, ExecutionRun
from packages.domain.models.common import utc_now
from packages.execution import ExecutionRequest, ExecutionResult
from packages.storage.base import ExecutionArtifactStore, ExecutionRunStore


class ExecutionLogService:
    def __init__(self, run_store: ExecutionRunStore, artifact_store: ExecutionArtifactStore) -> None:
        self.run_store = run_store
        self.artifact_store = artifact_store

    def record_result(self, request: ExecutionRequest, result: ExecutionResult) -> ExecutionRun:
        run = ExecutionRun(
            project_id=request.project.project_id,
            task_id=request.task.task_id,
            backend=result.backend,
            command=request.command,
            status=result.status,
            summary=result.summary,
            started_at=utc_now(),
            finished_at=utc_now(),
            logs=list(result.logs),
            metadata={**request.metadata, **result.metadata},
        )
        persisted = self.run_store.upsert_execution_run(run)
        artifacts = self._persist_log_artifacts(persisted, result.logs)
        if artifacts:
            persisted = persisted.model_copy(
                update={
                    "artifact_ids": [item.artifact_id for item in artifacts],
                    "updated_at": utc_now(),
                }
            )
            persisted = self.run_store.upsert_execution_run(persisted)
        return persisted

    def list_runs(self, project_id: str, task_id: str | None = None) -> list[ExecutionRun]:
        return self.run_store.list_execution_runs(project_id, task_id=task_id)

    def list_artifacts(
        self,
        project_id: str,
        execution_id: str | None = None,
        task_id: str | None = None,
    ) -> list[ExecutionArtifact]:
        return self.artifact_store.list_execution_artifacts(
            project_id,
            execution_id=execution_id,
            task_id=task_id,
        )

    def read_artifact(self, project_id: str, artifact_id: str) -> bytes | None:
        return self.artifact_store.read_execution_artifact(project_id, artifact_id)

    def _persist_log_artifacts(self, run: ExecutionRun, logs: Iterable[str]) -> list[ExecutionArtifact]:
        artifacts: list[ExecutionArtifact] = []
        for index, log_text in enumerate(logs, start=1):
            if not log_text.strip():
                continue
            artifact = ExecutionArtifact(
                execution_id=run.execution_id,
                project_id=run.project_id,
                task_id=run.task_id,
                name=f"log-{index}.txt",
                relative_path="",
                size_bytes=0,
                content_type="text/plain; charset=utf-8",
                metadata={"kind": "execution-log", "line_count": len(log_text.splitlines())},
            )
            created = self.artifact_store.create_execution_artifact(
                artifact,
                log_text.encode("utf-8"),
            )
            artifacts.append(created)
        return artifacts
