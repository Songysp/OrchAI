from __future__ import annotations

from packages.agents.base import AgentAdapter, AgentTurnRequest, AgentTurnResult


class CodexAdapter(AgentAdapter):
    provider_name = "codex"

    async def run_turn(self, request: AgentTurnRequest) -> AgentTurnResult:
        return AgentTurnResult(
            role=request.role,
            provider=self.provider_name,
            model=request.project.agent_mapping.get(request.role).model if request.role in request.project.agent_mapping else None,
            output="Codex adapter skeleton: provider wiring will be added in a later phase.",
            metadata={"status": "stub"},
        )
