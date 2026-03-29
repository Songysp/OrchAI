from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from packages.agents import AgentFactory, ClaudeAdapter
from packages.config import ConfigLoader, ConfigService, LoadedConfig, PlatformConfig, RuntimeConfig
from packages.config.models import ClaudeRuntimeConfig, CodexRuntimeConfig, GeminiRuntimeConfig
from packages.domain.models import AgentMapping, Project


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_config_loader_defaults_to_cli_runtime_without_config_json(tmp_path: Path) -> None:
    loaded = ConfigLoader(tmp_path).load()

    assert loaded.runtime.claude.mode == "cli"
    assert loaded.runtime.claude.default_model is None
    assert loaded.runtime.claude.cli.command == "claude"
    assert loaded.runtime.claude.cli.timeout == 120


def test_config_loader_reads_config_json_runtime(tmp_path: Path) -> None:
    _write_text(
        tmp_path / "config.json",
        json.dumps(
            {
                "claude": {
                    "mode": "api",
                    "default_model": "claude-3-7-sonnet",
                    "cli": {"command": "claude-dev", "timeout": 45},
                    "api": {"api_key_env": "CLAUDE_API_KEY"},
                }
            }
        ),
    )

    loaded = ConfigLoader(tmp_path).load()

    assert loaded.runtime.claude.mode == "api"
    assert loaded.runtime.claude.default_model == "claude-3-7-sonnet"
    assert loaded.runtime.claude.cli.command == "claude-dev"
    assert loaded.runtime.claude.cli.timeout == 45
    assert loaded.runtime.claude.api.api_key_env == "CLAUDE_API_KEY"


def test_config_loader_rejects_invalid_claude_mode(tmp_path: Path) -> None:
    _write_text(tmp_path / "config.json", json.dumps({"claude": {"mode": "sdk"}}))

    with pytest.raises(ValidationError):
        ConfigLoader(tmp_path).load()


def test_config_service_resolves_cli_defaults_and_model() -> None:
    loaded_config = LoadedConfig(
        platform=PlatformConfig(),
        runtime=RuntimeConfig(
            claude=ClaudeRuntimeConfig(
                mode="cli",
                default_model="claude-sonnet",
                cli={"command": "claude-local", "timeout": 30},
            )
        ),
    )
    service = ConfigService(loaded_config)

    resolved = service.resolve_claude_config(model=None)

    assert resolved.mode == "cli"
    assert resolved.model == "claude-sonnet"
    assert resolved.parameters == {
        "driver_mode": "cli",
        "command": "claude-local",
        "timeout": 30,
    }


def test_config_service_allows_api_override_from_project_parameters(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    loaded_config = LoadedConfig(
        platform=PlatformConfig(),
        runtime=RuntimeConfig(claude=ClaudeRuntimeConfig(mode="cli", default_model="claude-sonnet")),
    )
    service = ConfigService(loaded_config)

    resolved = service.resolve_claude_config(parameters={"driver_mode": "api"}, model=None)

    assert resolved.mode == "api"
    assert resolved.parameters == {
        "driver_mode": "api",
        "api_key": "***",
        "api_key_env": "ANTHROPIC_API_KEY",
    }


def test_config_service_rejects_api_mode_without_available_key() -> None:
    loaded_config = LoadedConfig(
        platform=PlatformConfig(),
        runtime=RuntimeConfig(claude=ClaudeRuntimeConfig(mode="api")),
    )
    service = ConfigService(loaded_config)

    with pytest.raises(ValueError, match="Claude API mode requires"):
        service.resolve_claude_config(model=None)


def test_agent_factory_inherits_claude_default_model() -> None:
    project = Project(
        project_id="project-agents",
        repo_url="https://github.com/example/project-agents",
        workspace_path="workspaces/project-agents",
        chat_platform="slack",
        agent_mapping={
            "representative": AgentMapping(
                role="representative",
                provider="claude",
                parameters={"temperature": 0.2},
            ),
        },
    )
    config_service = ConfigService(
        LoadedConfig(
            platform=PlatformConfig(),
            runtime=RuntimeConfig(claude=ClaudeRuntimeConfig(default_model="claude-config-default")),
        )
    )
    factory = AgentFactory({"claude": ClaudeAdapter()}, config_service=config_service)

    _, selection = factory.get_agent("representative", project)

    assert selection.model == "claude-config-default"
    assert selection.parameters["temperature"] == 0.2


def test_config_service_resolves_gemini_runtime(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "gemini-key")
    service = ConfigService(
        LoadedConfig(
            platform=PlatformConfig(),
            runtime=RuntimeConfig(gemini=GeminiRuntimeConfig(default_model="gemini-2.5-pro")),
        )
    )

    resolved = service.resolve_gemini_config(model=None)

    assert resolved.provider == "gemini"
    assert resolved.model == "gemini-2.5-pro"
    assert resolved.api_key_env == "GEMINI_API_KEY"
    assert resolved.parameters["api_key"] == "***"


def test_config_service_resolves_codex_runtime(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "openai-key")
    service = ConfigService(
        LoadedConfig(
            platform=PlatformConfig(),
            runtime=RuntimeConfig(codex=CodexRuntimeConfig(default_model="gpt-5.1")),
        )
    )

    resolved = service.resolve_codex_config(model=None)

    assert resolved.provider == "codex"
    assert resolved.model == "gpt-5.1"
    assert resolved.api_key_env == "OPENAI_API_KEY"
    assert resolved.parameters["api_key"] == "***"
