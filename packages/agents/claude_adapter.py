from __future__ import annotations

from packages.agents.base import AgentAdapter, AgentTurnRequest, AgentTurnResult
from packages.agents.drivers.claude_cli import ClaudeCLIDriver
from packages.agents.drivers.claude_api import ClaudeAPIDriver
from packages.config.service import ConfigService


class ClaudeAdapter(AgentAdapter):
    """Hybrid adapter that resolves Claude runtime defaults before selecting a driver."""

    provider_name = "claude"

    def __init__(self, config_service: ConfigService | None = None) -> None:
        self.config_service = config_service

    async def run_turn(self, request: AgentTurnRequest) -> AgentTurnResult:
        params = request.agent_selection.parameters
        resolved = (
            self.config_service.resolve_claude_config(params, model=request.agent_selection.model)
            if self.config_service
            else None
        )
        mode = resolved.mode if resolved is not None else params.get("driver_mode", "cli")
        if mode not in {"cli", "api"}:
            raise ValueError("Unknown Claude driver mode. Valid options: 'cli' and 'api'.")

        if mode == "cli":
            timeout = resolved.timeout if resolved is not None else int(params.get("timeout", 120))
            command = resolved.cli_command if resolved is not None else str(params.get("command", "claude"))
            driver = ClaudeCLIDriver(timeout=timeout, command=command)
        else:  # "api"
            api_key = resolved.api_key if resolved is not None else params.get("api_key")
            driver = ClaudeAPIDriver(api_key=api_key)

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
                "driver_mode": str(mode),
                "parameters": resolved.parameters if resolved is not None else params,
            },
        )
