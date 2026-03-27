from __future__ import annotations

from packages.agents.base import AgentAdapter, AgentTurnRequest, AgentTurnResult


class CodexAdapter(AgentAdapter):
    provider_name = "codex"

    async def run_turn(self, request: AgentTurnRequest) -> AgentTurnResult:
        mapping = request.project.agent_mapping.get(request.role)
        return AgentTurnResult(
            role=request.role,
            provider=self.provider_name,
            model=mapping.model if mapping is not None else None,
            output=f"{request.role.capitalize()} mock response from Codex based on prompt: {request.prompt}",
            metadata={"status": "stub", "provider_mode": "mock"},
        )
