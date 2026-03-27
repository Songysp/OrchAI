from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from apps.orchestrator.api.deps import get_orchestrator_service
from packages.domain.models import TaskStatus
from packages.domain.services.orchestrator import CreateTaskInput, OrchestratorService

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("")
def list_tasks(
    project_id: str | None = Query(default=None),
    service: OrchestratorService = Depends(get_orchestrator_service),
):
    return service.list_tasks(project_id)


@router.post("")
def create_task(payload: CreateTaskInput, service: OrchestratorService = Depends(get_orchestrator_service)):
    if service.get_project(payload.project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return service.create_task(payload)


@router.post("/{task_id}/status/{status}")
def update_task_status(
    task_id: str,
    status: TaskStatus,
    service: OrchestratorService = Depends(get_orchestrator_service),
):
    task = service.update_task_status(task_id, status)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task
