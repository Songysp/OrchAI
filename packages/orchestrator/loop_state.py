from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class PhaseResult(BaseModel):
    """Result of a specific orchestration phase."""
    role: str
    turn_number: int
    output: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class LoopState(BaseModel):
    """Persistent state of the orchestration loop."""
    max_turns: int = 5
    turn_count: int = 0
    is_complete: bool = False
    phases: List[PhaseResult] = Field(default_factory=list)
    escalation_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def add_phase_result(self, result: PhaseResult):
        self.phases.append(result)

    def mark_complete(self):
        self.is_complete = True

    def escalate(self, message: str):
        self.escalation_message = message

    def is_max_turns_exceeded(self) -> bool:
        return self.turn_count >= self.max_turns
