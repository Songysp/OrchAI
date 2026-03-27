from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from apps.orchestrator.api.deps import get_orchestrator_service
from apps.orchestrator.api.models import ConversationListResponse, ConversationMessageResponse, ConversationThreadResponse
from apps.orchestrator.services.orchestrator_service import OrchestratorService

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("", response_model=ConversationListResponse)
def list_conversations(
    project_id: str | None = Query(default=None),
    task_id: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    service: OrchestratorService = Depends(get_orchestrator_service),
) -> ConversationListResponse:
    conversations = service.list_conversations(project_id)
    if task_id is not None:
        conversations = [item for item in conversations if item.task_id == task_id]
    paged = conversations[offset : offset + limit]
    return ConversationListResponse(
        items=[
            ConversationThreadResponse(
                conversation_id=item.conversation_id,
                project_id=item.project_id,
                task_id=item.task_id,
                domain=item.domain.value,
                title=item.title,
                summary=item.summary,
                created_at=item.created_at,
                updated_at=item.updated_at,
                messages=[
                    ConversationMessageResponse(
                        message_id=message.message_id,
                        project_id=message.project_id,
                        domain=message.domain.value,
                        role=message.role,
                        content=message.content,
                        envelope=message.envelope.model_dump(mode="json") if message.envelope is not None else None,
                        metadata=message.metadata,
                    )
                    for message in item.messages
                ],
            )
            for item in paged
        ],
        total=len(conversations),
        limit=limit,
        offset=offset,
    )
