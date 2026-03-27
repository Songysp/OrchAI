from __future__ import annotations

from packages.agents.base import AgentAdapter, AgentTurnRequest, AgentTurnResult


class ClaudeAdapter(AgentAdapter):
    provider_name = "claude"

    async def run_turn(self, request: AgentTurnRequest) -> AgentTurnResult:
        return AgentTurnResult(
            role=request.role,
            provider=self.provider_name,
            model=request.agent_selection.model,
            output=f"{request.role.capitalize()} mock response from Claude based on prompt: {request.prompt}",
            metadata={
                "status": "stub",
                "provider_mode": "mock",
                "parameters": request.agent_selection.parameters,
            },
        )
