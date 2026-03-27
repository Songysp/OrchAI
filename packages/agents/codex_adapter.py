from __future__ import annotations

from packages.agents.base import AgentAdapter, AgentTurnRequest, AgentTurnResult


class CodexAdapter(AgentAdapter):
    provider_name = "codex"

    async def run_turn(self, request: AgentTurnRequest) -> AgentTurnResult:
        return AgentTurnResult(
            role=request.role,
            provider=self.provider_name,
            model=request.agent_selection.model,
            output=f"{request.role.capitalize()} mock response from Codex based on prompt: {request.prompt}",
            metadata={
                "status": "stub",
                "provider_mode": "mock",
                "parameters": request.agent_selection.parameters,
            },
        )
