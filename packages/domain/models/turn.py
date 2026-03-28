from __future__ import annotations
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

class TurnResult(BaseModel):
    """Persistent domain model for an agent turn result."""
    turn_id: str = Field(description="Unique ID for this turn")
    run_id: str = Field(description="Orchestrator run ID")
    turn_index: int = Field(description="Sequence number in the run")
    role: str = Field(description="Agent role (planner, worker, refiner, etc.)")
    prompt: str = Field(description="Full prompt sent to the agent")
    output: str = Field(description="Agent's response content")
    status: str = Field(default="completed", description="Turn status (completed, failed, escalated)")
    started_at: datetime = Field(default_factory=datetime.now)
    finished_at: Optional[datetime] = None
    completion_reason: Optional[str] = None
    escalation_context: Optional[str] = Field(None, description="Detailed context when escalated for human intervention")
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
