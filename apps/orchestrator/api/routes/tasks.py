from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from apps.orchestrator.api.deps import get_orchestrator_service
from apps.orchestrator.api.models import CreateTaskRequest, TaskRunResponse, TaskStatusResponse
from apps.orchestrator.services.orchestrator_service import OrchestratorService

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", response_model=TaskRunResponse)
async def create_task(
    payload: CreateTaskRequest,
    service: OrchestratorService = Depends(get_orchestrator_service),
) -> TaskRunResponse:
    if service.get_project(payload.project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")

    created = service.create_task(project_id=payload.project_id, user_input=payload.user_input)
    result = await service.run_task(created.task_id)

    return TaskRunResponse(
        task_id=result.task_id,
        project_id=result.project_id,
        title=created.title,
        final_status=result.final_status.value,
        final_stage=result.final_stage.value,
        summary=result.representative_summary,
        decision_id=result.decision_id,
        approval_required=result.approval_required,
        approval_id=result.approval_id,
    )


@router.get("/{task_id}", response_model=TaskStatusResponse)
def get_task_status(
    task_id: str,
    service: OrchestratorService = Depends(get_orchestrator_service),
) -> TaskStatusResponse:
    status = service.get_task_status(task_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Task not found")

    return TaskStatusResponse(
        task_id=status.task_id,
        project_id=status.project_id,
        status=status.status.value,
        stage=status.stage.value,
        updated_at=status.updated_at,
        summary=status.summary,
    )
