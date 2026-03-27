from __future__ import annotations

from pathlib import Path

import yaml

from packages.config.models import LoadedConfig, PlatformConfig
from packages.domain.models import Project


class ConfigLoader:
    def __init__(self, root_path: Path) -> None:
        self.root_path = root_path

    def load(self) -> LoadedConfig:
        platform = self._load_platform_config()
        projects = self._load_projects(platform.paths.projects_dir)
        return LoadedConfig(platform=platform, projects=projects)

    def _load_platform_config(self) -> PlatformConfig:
        config_path = self.root_path / "configs" / "platform.yaml"
        if not config_path.exists():
            return PlatformConfig()

        data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        return PlatformConfig.model_validate(data)

    def _load_projects(self, relative_projects_dir: Path) -> list[Project]:
        projects_dir = self.root_path / relative_projects_dir
        if not projects_dir.exists():
            return []

        projects: list[Project] = []
        for config_path in sorted(projects_dir.glob("*.yaml")):
            data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
            projects.append(Project.model_validate(data))
        return projects
