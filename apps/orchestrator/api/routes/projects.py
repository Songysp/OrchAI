from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from apps.orchestrator.api.deps import get_orchestrator_service
from packages.domain.services.orchestrator import OrchestratorService

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("")
def list_projects(service: OrchestratorService = Depends(get_orchestrator_service)):
    return service.list_projects()


@router.get("/{project_id}")
def get_project(project_id: str, service: OrchestratorService = Depends(get_orchestrator_service)):
    project = service.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project
