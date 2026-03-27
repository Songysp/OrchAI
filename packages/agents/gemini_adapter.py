from __future__ import annotations

from packages.agents.base import AgentAdapter, AgentTurnRequest, AgentTurnResult


class GeminiAdapter(AgentAdapter):
    provider_name = "gemini"

    async def run_turn(self, request: AgentTurnRequest) -> AgentTurnResult:
        return AgentTurnResult(
            role=request.role,
            provider=self.provider_name,
            model=request.agent_selection.model,
            output=f"{request.role.capitalize()} mock response from Gemini based on prompt: {request.prompt}",
            metadata={
                "status": "stub",
                "provider_mode": "mock",
                "parameters": request.agent_selection.parameters,
            },
        )
