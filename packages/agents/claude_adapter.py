from __future__ import annotations

from packages.agents.base import AgentAdapter, AgentTurnRequest, AgentTurnResult


class ClaudeAdapter(AgentAdapter):
    provider_name = "claude"

    async def run_turn(self, request: AgentTurnRequest) -> AgentTurnResult:
        mapping = request.project.agent_mapping.get(request.role)
        return AgentTurnResult(
            role=request.role,
            provider=self.provider_name,
            model=mapping.model if mapping is not None else None,
            output=f"{request.role.capitalize()} mock response from Claude based on prompt: {request.prompt}",
            metadata={"status": "stub", "provider_mode": "mock"},
        )
