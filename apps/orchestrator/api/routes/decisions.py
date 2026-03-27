from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from apps.orchestrator.api.deps import get_orchestrator_service
from apps.orchestrator.services.orchestrator_service import OrchestratorService
from packages.domain.models import Decision

router = APIRouter(prefix="/decisions", tags=["decisions"])


@router.get("")
def list_decisions(
    project_id: str | None = Query(default=None),
    service: OrchestratorService = Depends(get_orchestrator_service),
):
    return service.list_decisions(project_id)


@router.post("")
def create_decision(payload: Decision, service: OrchestratorService = Depends(get_orchestrator_service)):
    return service.record_decision(payload)
