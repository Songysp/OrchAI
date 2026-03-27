from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

from packages.domain.models import Project


class PlatformPaths(BaseModel):
    data_dir: Path = Path("data")
    projects_dir: Path = Path("configs/projects")
    workspaces_dir: Path = Path("workspaces")


class PlatformConfig(BaseModel):
    app_name: str = "AI Dev Team Platform"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    paths: PlatformPaths = Field(default_factory=PlatformPaths)


class LoadedConfig(BaseModel):
    platform: PlatformConfig
    projects: list[Project] = Field(default_factory=list)
