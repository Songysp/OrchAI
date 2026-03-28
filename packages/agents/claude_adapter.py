from __future__ import annotations

from packages.agents.base import AgentAdapter, AgentTurnRequest, AgentTurnResult
from packages.agents.drivers.claude_cli import ClaudeCLIDriver
from packages.agents.drivers.claude_api import ClaudeAPIDriver

_VALID_MODES = ("cli", "api")


class ClaudeAdapter(AgentAdapter):
    """Hybrid adapter: delegates to ClaudeCLIDriver (default) or ClaudeAPIDriver
    based on agent_selection.parameters["driver_mode"].
    """

    provider_name = "claude"

    async def run_turn(self, request: AgentTurnRequest) -> AgentTurnResult:
        params = request.agent_selection.parameters
        mode = params.get("driver_mode", "cli")

        if mode not in _VALID_MODES:
            raise ValueError(
                f"Unknown driver_mode '{mode}'. Valid options: {_VALID_MODES}"
            )

        if mode == "cli":
            timeout = int(params.get("timeout", 120))
            driver = ClaudeCLIDriver(timeout=timeout)
        else:  # "api"
            driver = ClaudeAPIDriver(api_key=params.get("api_key"))

        output = await driver.prompt(
            text=request.prompt,
            model=request.agent_selection.model,
        )

        return AgentTurnResult(
            role=request.role,
            provider=self.provider_name,
            model=request.agent_selection.model,
            output=output,
            metadata={
                "driver_mode": mode,
                "parameters": params,
            },
        )
