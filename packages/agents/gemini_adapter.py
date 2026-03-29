from __future__ import annotations

from packages.agents.base import AgentAdapter, AgentTurnRequest, AgentTurnResult
from packages.agents.drivers.gemini_cli import GeminiCLIDriver
from packages.agents.drivers.gemini_api import GeminiAPIDriver
from packages.config.service import ConfigService


class GeminiAdapter(AgentAdapter):
    provider_name = "gemini"

    def __init__(self, config_service: ConfigService | None = None) -> None:
        self.config_service = config_service

    async def run_turn(self, request: AgentTurnRequest) -> AgentTurnResult:
        params = request.agent_selection.parameters
        resolved = (
            self.config_service.resolve_gemini_config(parameters=params, model=request.agent_selection.model)
            if self.config_service
            else None
        )
        mode = resolved.mode if resolved is not None else params.get("driver_mode", "cli")
        if mode == "cli":
            driver = GeminiCLIDriver(
                timeout=resolved.timeout if resolved is not None and resolved.timeout is not None else 120,
                command=resolved.cli_command if resolved is not None and resolved.cli_command is not None else "gemini",
            )
        else:
            driver = GeminiAPIDriver(api_key=resolved.api_key if resolved is not None else None)
        output = await driver.prompt(
            text=request.prompt,
            model=resolved.model if resolved is not None else request.agent_selection.model,
            cwd=request.project.workspace_path,
        )

        return AgentTurnResult(
            role=request.role,
            provider=self.provider_name,
            model=resolved.model if resolved is not None else request.agent_selection.model,
            output=output,
            metadata={
                "driver_mode": mode,
                "parameters": resolved.parameters if resolved is not None else request.agent_selection.parameters,
            },
        )
