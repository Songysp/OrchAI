from __future__ import annotations

import os
from typing import Any

from pydantic import BaseModel, Field

from packages.config.models import (
    ClaudeDriverMode,
    ClaudeRuntimeConfig,
    CodexRuntimeConfig,
    GeminiRuntimeConfig,
    LoadedConfig,
    ProviderDriverMode,
)


class ResolvedClaudeConfig(BaseModel):
    mode: ClaudeDriverMode
    model: str | None = None
    cli_command: str = "claude"
    timeout: int = 120
    api_key: str | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)


class ResolvedProviderAPIConfig(BaseModel):
    provider: str
    mode: ProviderDriverMode
    model: str | None = None
    cli_command: str | None = None
    timeout: int | None = None
    api_key: str | None = None
    api_key_env: str | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)


class ConfigService:
    def __init__(self, loaded_config: LoadedConfig) -> None:
        self.loaded_config = loaded_config

    def resolve_agent_model(self, provider: str, model: str | None) -> str | None:
        if model is not None:
            return model

        if provider == "claude":
            return self.loaded_config.runtime.claude.default_model
        if provider == "gemini":
            return self.loaded_config.runtime.gemini.default_model
        if provider == "codex":
            return self.loaded_config.runtime.codex.default_model
        return model

    def resolve_claude_config(
        self,
        parameters: dict[str, Any] | None = None,
        model: str | None = None,
    ) -> ResolvedClaudeConfig:
        merged_parameters = self._merge_claude_parameters(parameters or {})
        runtime = ClaudeRuntimeConfig.model_validate(merged_parameters)
        api_key = runtime.api.api_key or os.getenv(runtime.api.api_key_env)
        if runtime.mode == "api" and not api_key:
            raise ValueError(
                "Claude API mode requires a configured API key or an environment variable "
                f"named '{runtime.api.api_key_env}'."
            )
        return ResolvedClaudeConfig(
            mode=runtime.mode,
            model=self.resolve_agent_model("claude", model),
            cli_command=runtime.cli.command,
            timeout=runtime.cli.timeout,
            api_key=api_key,
            parameters=self._resolved_parameters(runtime=runtime, api_key=api_key),
        )

    def resolve_gemini_config(
        self,
        parameters: dict[str, Any] | None = None,
        model: str | None = None,
    ) -> ResolvedProviderAPIConfig:
        return self._resolve_simple_provider_config(
            provider="gemini",
            runtime=self.loaded_config.runtime.gemini,
            parameters=parameters or {},
            model=model,
        )

    def resolve_codex_config(
        self,
        parameters: dict[str, Any] | None = None,
        model: str | None = None,
    ) -> ResolvedProviderAPIConfig:
        return self._resolve_simple_provider_config(
            provider="codex",
            runtime=self.loaded_config.runtime.codex,
            parameters=parameters or {},
            model=model,
        )

    def _merge_claude_parameters(self, parameters: dict[str, Any]) -> dict[str, Any]:
        claude_defaults = self.loaded_config.runtime.claude.model_dump(mode="python")

        mode = parameters.get("driver_mode", claude_defaults["mode"])
        merged: dict[str, Any] = {
            "mode": mode,
            "cli": dict(claude_defaults["cli"]),
            "api": dict(claude_defaults["api"]),
        }

        if "timeout" in parameters:
            merged["cli"]["timeout"] = parameters["timeout"]
        if "command" in parameters:
            merged["cli"]["command"] = parameters["command"]

        if "api_key" in parameters:
            merged["api"]["api_key"] = parameters["api_key"]
        if "api_key_env" in parameters:
            merged["api"]["api_key_env"] = parameters["api_key_env"]

        return merged

    def _resolved_parameters(self, runtime: ClaudeRuntimeConfig, api_key: str | None) -> dict[str, Any]:
        if runtime.mode == "cli":
            return {
                "driver_mode": runtime.mode,
                "command": runtime.cli.command,
                "timeout": runtime.cli.timeout,
            }

        return {
            "driver_mode": runtime.mode,
            "api_key": "***" if api_key else None,
            "api_key_env": runtime.api.api_key_env,
        }

    def _resolve_simple_provider_config(
        self,
        *,
        provider: str,
        runtime: GeminiRuntimeConfig | CodexRuntimeConfig,
        parameters: dict[str, Any],
        model: str | None,
    ) -> ResolvedProviderAPIConfig:
        mode = parameters.get("driver_mode", runtime.mode)
        resolved_model = model or runtime.default_model
        if mode == "cli":
            command = str(parameters.get("command", runtime.cli.command))
            timeout = int(parameters.get("timeout", runtime.cli.timeout))
            return ResolvedProviderAPIConfig(
                provider=provider,
                mode="cli",
                model=resolved_model,
                cli_command=command,
                timeout=timeout,
                parameters={
                    "driver_mode": "cli",
                    "command": command,
                    "timeout": timeout,
                },
            )

        api_key_env = str(parameters.get("api_key_env", runtime.api.api_key_env))
        api_key = parameters.get("api_key") or runtime.api.api_key or os.getenv(api_key_env)
        if not api_key:
            raise ValueError(
                f"{provider.capitalize()} API mode requires a configured API key or an environment variable "
                f"named '{api_key_env}'."
            )
        return ResolvedProviderAPIConfig(
            provider=provider,
            mode="api",
            model=resolved_model,
            api_key=api_key,
            api_key_env=api_key_env,
            parameters={
                "driver_mode": "api",
                "api_key": "***",
                "api_key_env": api_key_env,
            },
        )
