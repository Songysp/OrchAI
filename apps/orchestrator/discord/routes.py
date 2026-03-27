from __future__ import annotations

import json
import os

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from apps.orchestrator.api.deps import get_chat_ingress_service, get_orchestrator_service
from apps.orchestrator.discord.service import DiscordEventTranslator
from apps.orchestrator.services.chat_ingress_service import ChatIngressService
from apps.orchestrator.services.orchestrator_service import OrchestratorService

try:
    from nacl.exceptions import BadSignatureError
    from nacl.signing import VerifyKey
except Exception:  # pragma: no cover - optional dependency at runtime
    BadSignatureError = Exception
    VerifyKey = None

router = APIRouter(prefix="/integrations/discord", tags=["discord"])

translator = DiscordEventTranslator()


class DiscordIngressResponse(BaseModel):
    accepted: bool
    action: str
    message: str
    task_id: str | None = None
    status: str | None = None
    approval_id: str | None = None
    resumed: bool = False


def _verify_discord_signature(
    *,
    body: bytes,
    timestamp: str | None,
    signature: str | None,
    public_key: str,
) -> bool:
    if not timestamp or not signature:
        return False
    if VerifyKey is None:
        raise RuntimeError("PyNaCl is required for Discord signature verification")

    try:
        verify_key = VerifyKey(bytes.fromhex(public_key))
        signature_bytes = bytes.fromhex(signature)
    except ValueError:
        return False

    message = timestamp.encode("utf-8") + body
    try:
        verify_key.verify(message, signature_bytes)
    except BadSignatureError:
        return False
    return True


@router.post("/{project_id}/events", response_model=DiscordIngressResponse)
async def receive_discord_event(
    project_id: str,
    request: Request,
    ingress: ChatIngressService = Depends(get_chat_ingress_service),
    orchestrator: OrchestratorService = Depends(get_orchestrator_service),
) -> DiscordIngressResponse | JSONResponse:
    project = orchestrator.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.chat_platform.lower() != "discord":
        raise HTTPException(status_code=400, detail="Project is not configured for Discord")

    public_key = os.getenv("DISCORD_PUBLIC_KEY")
    raw_body = await request.body()
    if public_key:
        try:
            is_verified = _verify_discord_signature(
                body=raw_body,
                timestamp=request.headers.get("X-Signature-Timestamp"),
                signature=request.headers.get("X-Signature-Ed25519"),
                public_key=public_key,
            )
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        if not is_verified:
            raise HTTPException(status_code=401, detail="Invalid Discord signature")

    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON payload") from exc
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Discord payload must be a JSON object")

    if payload.get("type") == 1:
        return JSONResponse(content={"type": 1})

    try:
        event = translator.translate(project, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if event is None:
        return DiscordIngressResponse(
            accepted=True,
            action="ignored",
            message="Discord event was ignored by the placeholder transport handler.",
        )

    result = await ingress.handle_event(event)
    return DiscordIngressResponse(
        accepted=result.accepted,
        action=result.action,
        message=result.message,
        task_id=result.task_result.task_id if result.task_result else result.task_id,
        status=result.task_result.final_status.value if result.task_result else result.task_status,
        approval_id=result.approval_id,
        resumed=result.resumed,
    )
