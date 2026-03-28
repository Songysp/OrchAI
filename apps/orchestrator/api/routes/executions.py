from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from apps.orchestrator.api.deps import get_orchestrator_service
from apps.orchestrator.api.models import (
    ExecutionArtifactListResponse,
    ExecutionArtifactResponse,
    ExecutionRunListResponse,
    ExecutionRunResponse,
)
from apps.orchestrator.services.orchestrator_service import OrchestratorService

router = APIRouter(prefix="/executions", tags=["executions"])


@router.get("", response_model=ExecutionRunListResponse)
def list_execution_runs(
    project_id: str | None = Query(default=None),
    task_id: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    service: OrchestratorService = Depends(get_orchestrator_service),
) -> ExecutionRunListResponse:
    runs = sorted(
        service.list_execution_runs(project_id=project_id, task_id=task_id),
        key=lambda item: item.created_at,
        reverse=True,
    )
    paged = runs[offset : offset + limit]
    return ExecutionRunListResponse(
        items=[
            ExecutionRunResponse(
                execution_id=item.execution_id,
                project_id=item.project_id,
                task_id=item.task_id,
                backend=item.backend.value,
                command=item.command,
                status=item.status,
                summary=item.summary,
                started_at=item.started_at,
                finished_at=item.finished_at,
                logs=item.logs,
                artifact_ids=item.artifact_ids,
                metadata=item.metadata,
            )
            for item in paged
        ],
        total=len(runs),
        limit=limit,
        offset=offset,
    )


@router.get("/{execution_id}/artifacts", response_model=ExecutionArtifactListResponse)
def list_execution_artifacts(
    execution_id: str,
    project_id: str | None = Query(default=None),
    task_id: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    service: OrchestratorService = Depends(get_orchestrator_service),
) -> ExecutionArtifactListResponse:
    artifacts = sorted(
        service.list_execution_artifacts(
            project_id=project_id,
            execution_id=execution_id,
            task_id=task_id,
        ),
        key=lambda item: item.created_at,
        reverse=True,
    )
    paged = artifacts[offset : offset + limit]
    return ExecutionArtifactListResponse(
        items=[
            ExecutionArtifactResponse(
                artifact_id=item.artifact_id,
                execution_id=item.execution_id,
                project_id=item.project_id,
                task_id=item.task_id,
                name=item.name,
                relative_path=item.relative_path,
                size_bytes=item.size_bytes,
                content_type=item.content_type,
                created_at=item.created_at,
                metadata=item.metadata,
            )
            for item in paged
        ],
        total=len(artifacts),
        limit=limit,
        offset=offset,
    )
