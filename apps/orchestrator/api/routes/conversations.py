from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from apps.orchestrator.api.deps import get_orchestrator_service
from apps.orchestrator.services.orchestrator_service import OrchestratorService

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("")
def list_conversations(
    project_id: str | None = Query(default=None),
    service: OrchestratorService = Depends(get_orchestrator_service),
):
    return service.list_conversations(project_id)
