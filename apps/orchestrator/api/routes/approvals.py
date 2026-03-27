from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from apps.orchestrator.api.deps import get_orchestrator_service
from apps.orchestrator.api.models import ApprovalActionRequest, ApprovalActionResponse, ApprovalResponse
from apps.orchestrator.services.orchestrator_service import OrchestratorService

router = APIRouter(prefix="/approvals", tags=["approvals"])


@router.get("", response_model=list[ApprovalResponse])
def list_approvals(
    project_id: str | None = Query(default=None),
    service: OrchestratorService = Depends(get_orchestrator_service),
):
    approvals = service.list_approvals(project_id)
    return [
        ApprovalResponse(
            approval_id=item.approval_id,
            task_id=item.task_id,
            project_id=item.project_id,
            status=item.status.value,
            approved_by=item.approved_by,
            comment=item.comment,
            created_at=item.created_at,
        )
        for item in approvals
    ]

@router.post("/{approval_id}/approve", response_model=ApprovalActionResponse)
async def approve_approval(
    approval_id: str,
    payload: ApprovalActionRequest,
    service: OrchestratorService = Depends(get_orchestrator_service),
) -> ApprovalActionResponse:
    result = await service.approve_approval(
        approval_id=approval_id,
        approved_by=payload.approved_by,
        comment=payload.comment,
        resume_task=payload.resume_task,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Approval not found")
    return ApprovalActionResponse(
        approval=ApprovalResponse(
            approval_id=result["approval"].approval_id,
            task_id=result["approval"].task_id,
            project_id=result["approval"].project_id,
            status=result["approval"].status.value,
            approved_by=result["approval"].approved_by,
            comment=result["approval"].comment,
            created_at=result["approval"].created_at,
        ),
        resumed=result["resumed"],
        task_id=result["task"].task_id,
        task_stage=result["task"].stage.value,
        task_status=result["task"].status.value,
    )


@router.post("/{approval_id}/reject", response_model=ApprovalActionResponse)
async def reject_approval(
    approval_id: str,
    payload: ApprovalActionRequest,
    service: OrchestratorService = Depends(get_orchestrator_service),
) -> ApprovalActionResponse:
    result = service.reject_approval(
        approval_id=approval_id,
        approved_by=payload.approved_by,
        comment=payload.comment,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Approval not found")
    return ApprovalActionResponse(
        approval=ApprovalResponse(
            approval_id=result["approval"].approval_id,
            task_id=result["approval"].task_id,
            project_id=result["approval"].project_id,
            status=result["approval"].status.value,
            approved_by=result["approval"].approved_by,
            comment=result["approval"].comment,
            created_at=result["approval"].created_at,
        ),
        resumed=False,
        task_id=result["task"].task_id,
        task_stage=result["task"].stage.value,
        task_status=result["task"].status.value,
    )
