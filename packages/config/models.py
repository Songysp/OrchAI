from __future__ import annotations

from typing import Literal
from pathlib import Path

from pydantic import BaseModel, Field, model_validator

from packages.domain.models import Project

ClaudeDriverMode = Literal["cli", "api"]


class PlatformPaths(BaseModel):
    data_dir: Path = Path("data")
    projects_dir: Path = Path("configs/projects")
    workspaces_dir: Path = Path("workspaces")


class PlatformConfig(BaseModel):
    app_name: str = "AI Dev Team Platform"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    paths: PlatformPaths = Field(default_factory=PlatformPaths)


class ClaudeCLIConfig(BaseModel):
    command: str = "claude"
    timeout: int = 120

    @model_validator(mode="after")
    def validate_timeout(self) -> "ClaudeCLIConfig":
        if not self.command.strip():
            raise ValueError("Claude CLI command cannot be blank.")
        if self.timeout <= 0:
            raise ValueError("Claude CLI timeout must be greater than 0.")
        return self


class ClaudeAPIConfig(BaseModel):
    api_key: str | None = None
    api_key_env: str = "ANTHROPIC_API_KEY"

    @model_validator(mode="after")
    def validate_api_credentials(self) -> "ClaudeAPIConfig":
        if self.api_key is not None and not self.api_key.strip():
            raise ValueError("Claude API key cannot be blank.")
        if not self.api_key_env.strip():
            raise ValueError("Claude API key env var name cannot be blank.")
        return self


class SimpleAPIConfig(BaseModel):
    api_key: str | None = None
    api_key_env: str

    @model_validator(mode="after")
    def validate_api_credentials(self) -> "SimpleAPIConfig":
        if self.api_key is not None and not self.api_key.strip():
            raise ValueError("API key cannot be blank.")
        if not self.api_key_env.strip():
            raise ValueError("API key env var name cannot be blank.")
        return self


class ClaudeRuntimeConfig(BaseModel):
    mode: ClaudeDriverMode = "cli"
    default_model: str | None = None
    cli: ClaudeCLIConfig = Field(default_factory=ClaudeCLIConfig)
    api: ClaudeAPIConfig = Field(default_factory=ClaudeAPIConfig)


class GeminiRuntimeConfig(BaseModel):
    default_model: str = "gemini-2.0-flash"
    api: SimpleAPIConfig = Field(default_factory=lambda: SimpleAPIConfig(api_key_env="GEMINI_API_KEY"))


class CodexRuntimeConfig(BaseModel):
    default_model: str = "gpt-5"
    api: SimpleAPIConfig = Field(default_factory=lambda: SimpleAPIConfig(api_key_env="OPENAI_API_KEY"))


class RuntimeConfig(BaseModel):
    claude: ClaudeRuntimeConfig = Field(default_factory=ClaudeRuntimeConfig)
    gemini: GeminiRuntimeConfig = Field(default_factory=GeminiRuntimeConfig)
    codex: CodexRuntimeConfig = Field(default_factory=CodexRuntimeConfig)


class LoadedConfig(BaseModel):
    platform: PlatformConfig
    runtime: RuntimeConfig = Field(default_factory=RuntimeConfig)
    projects: list[Project] = Field(default_factory=list)
