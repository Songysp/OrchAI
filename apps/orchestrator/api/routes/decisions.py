from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from apps.orchestrator.api.deps import get_orchestrator_service
from apps.orchestrator.api.models import DecisionListResponse, DecisionResponse
from apps.orchestrator.services.orchestrator_service import OrchestratorService
from packages.domain.models import Decision

router = APIRouter(prefix="/decisions", tags=["decisions"])


@router.get("", response_model=DecisionListResponse)
def list_decisions(
    project_id: str | None = Query(default=None),
    task_id: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    service: OrchestratorService = Depends(get_orchestrator_service),
) -> DecisionListResponse:
    decisions = service.list_decisions(project_id)
    if task_id is not None:
        decisions = [item for item in decisions if item.task_id == task_id]
    decisions = sorted(decisions, key=lambda item: item.created_at, reverse=True)
    paged = decisions[offset : offset + limit]
    return DecisionListResponse(
        items=[
            DecisionResponse(
                decision_id=item.decision_id,
                task_id=item.task_id,
                project_id=item.project_id,
                summary=item.summary,
                chosen_option=item.chosen_option,
                created_at=item.created_at,
            )
            for item in paged
        ],
        total=len(decisions),
        limit=limit,
        offset=offset,
    )


@router.post("")
def create_decision(payload: Decision, service: OrchestratorService = Depends(get_orchestrator_service)):
    return service.record_decision(payload)
