from __future__ import annotations

from packages.agents.base import AgentAdapter, AgentTurnRequest, AgentTurnResult


class GeminiAdapter(AgentAdapter):
    provider_name = "gemini"

    async def run_turn(self, request: AgentTurnRequest) -> AgentTurnResult:
        return AgentTurnResult(
            role=request.role,
            provider=self.provider_name,
            model=request.project.agent_mapping.get(request.role).model if request.role in request.project.agent_mapping else None,
            output="Gemini adapter skeleton: provider wiring will be added in a later phase.",
            metadata={"status": "stub"},
        )
