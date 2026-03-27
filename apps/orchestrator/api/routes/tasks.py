from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from apps.orchestrator.api.deps import get_orchestrator_service
from apps.orchestrator.api.models import (
    CreateTaskRequest,
    TaskListItemResponse,
    TaskListResponse,
    TaskRunResponse,
    TaskStatusResponse,
)
from apps.orchestrator.services.orchestrator_service import OrchestratorService

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=TaskListResponse)
def list_tasks(
    project_id: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    service: OrchestratorService = Depends(get_orchestrator_service),
) -> TaskListResponse:
    tasks = sorted(
        service.list_tasks(project_id),
        key=lambda item: item.created_at,
        reverse=True,
    )
    paged = tasks[offset : offset + limit]
    return TaskListResponse(
        items=[
            TaskListItemResponse(
                task_id=item.task_id,
                project_id=item.project_id,
                title=item.title,
                status=item.status.value,
                stage=item.stage.value,
                created_at=item.created_at,
                updated_at=item.updated_at,
                summary=item.metadata.get("status_summary")
                if isinstance(item.metadata.get("status_summary"), str)
                else None,
            )
            for item in paged
        ],
        total=len(tasks),
        limit=limit,
        offset=offset,
    )


@router.post("", response_model=TaskRunResponse)
async def create_task(
    payload: CreateTaskRequest,
    service: OrchestratorService = Depends(get_orchestrator_service),
) -> TaskRunResponse:
    if service.get_project(payload.project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")

    result = await service.handle_user_control_message(
        project_id=payload.project_id,
        user_input=payload.user_input,
    )

    return TaskRunResponse(
        task_id=result.task_id,
        project_id=result.project_id,
        title=result.title,
        final_status=result.final_status.value,
        final_stage=result.final_stage.value,
        summary=result.representative_summary,
        decision_id=result.decision_id,
        approval_required=result.approval_required,
        approval_id=result.approval_id,
        chat_delivery_count=len(result.chat_deliveries),
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
