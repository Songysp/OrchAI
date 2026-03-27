from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from apps.orchestrator.api.deps import get_orchestrator_service
from packages.domain.services.orchestrator import CreateApprovalInput, OrchestratorService

router = APIRouter(prefix="/approvals", tags=["approvals"])


@router.get("")
def list_approvals(
    project_id: str | None = Query(default=None),
    service: OrchestratorService = Depends(get_orchestrator_service),
):
    return service.list_approvals(project_id)


@router.post("")
def create_approval(payload: CreateApprovalInput, service: OrchestratorService = Depends(get_orchestrator_service)):
    if service.get_project(payload.project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return service.create_approval(payload)
