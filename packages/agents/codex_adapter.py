from __future__ import annotations

from packages.agents.base import AgentAdapter, AgentTurnRequest, AgentTurnResult
from packages.agents.drivers.codex_api import CodexAPIDriver
from packages.config.service import ConfigService


class CodexAdapter(AgentAdapter):
    provider_name = "codex"

    def __init__(self, config_service: ConfigService | None = None) -> None:
        self.config_service = config_service

    async def run_turn(self, request: AgentTurnRequest) -> AgentTurnResult:
        resolved = (
            self.config_service.resolve_codex_config(model=request.agent_selection.model)
            if self.config_service
            else None
        )
        driver = CodexAPIDriver(api_key=resolved.api_key if resolved is not None else None)
        output = await driver.prompt(
            text=request.prompt,
            model=resolved.model if resolved is not None else request.agent_selection.model,
        )

        return AgentTurnResult(
            role=request.role,
            provider=self.provider_name,
            model=resolved.model if resolved is not None else request.agent_selection.model,
            output=output,
            metadata={
                "provider_mode": "api",
                "parameters": resolved.parameters if resolved is not None else request.agent_selection.parameters,
            },
        )
