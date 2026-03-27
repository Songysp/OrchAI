from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from apps.orchestrator.api.deps import get_chat_ingress_service, get_orchestrator_service
from apps.orchestrator.services.chat_ingress_service import ChatIngressService
from apps.orchestrator.services.orchestrator_service import OrchestratorService
from apps.orchestrator.slack.service import SlackEventTranslator

router = APIRouter(prefix="/integrations/slack", tags=["slack"])

translator = SlackEventTranslator()


class SlackIngressResponse(BaseModel):
    accepted: bool
    action: str
    message: str
    task_id: str | None = None
    status: str | None = None
    approval_id: str | None = None
    resumed: bool = False


@router.post("/{project_id}/events", response_model=SlackIngressResponse)
async def receive_slack_event(
    project_id: str,
    payload: dict[str, Any],
    ingress: ChatIngressService = Depends(get_chat_ingress_service),
    orchestrator: OrchestratorService = Depends(get_orchestrator_service),
) -> SlackIngressResponse:
    project = orchestrator.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.chat_platform.lower() != "slack":
        raise HTTPException(status_code=400, detail="Project is not configured for Slack")

    if payload.get("type") == "url_verification":
        challenge = payload.get("challenge")
        return SlackIngressResponse(
            accepted=True,
            action="url_verification",
            message=str(challenge or ""),
        )

    try:
        event = translator.translate(project, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if event is None:
        return SlackIngressResponse(
            accepted=True,
            action="ignored",
            message="Slack event was ignored by the placeholder transport handler.",
        )

    result = await ingress.handle_event(event)
    return SlackIngressResponse(
        accepted=result.accepted,
        action=result.action,
        message=result.message,
        task_id=result.task_result.task_id if result.task_result else result.task_id,
        status=result.task_result.final_status.value if result.task_result else result.task_status,
        approval_id=result.approval_id,
        resumed=result.resumed,
    )
