from __future__ import annotations

from packages.agents.base import AgentAdapter
from packages.domain.models import Project
from packages.domain.services.registry import PlatformRegistry


class ProjectRuntime:
    def __init__(self, registry: PlatformRegistry) -> None:
        self.registry = registry

    def get_project(self, project_id: str) -> Project:
        project = self.registry.project_store.get_project(project_id)
        if project is None:
            raise ValueError(f"Project '{project_id}' was not found.")
        return project

    def get_agent_adapter(self, project: Project, role: str) -> AgentAdapter:
        mapping = project.agent_mapping.get(role)
        if mapping is None:
            raise ValueError(f"Project '{project.project_id}' does not define an agent mapping for role '{role}'.")

        adapter = self.registry.agent_adapters.get(mapping.provider)
        if adapter is None:
            raise ValueError(
                f"Provider '{mapping.provider}' for role '{role}' is not registered for project '{project.project_id}'."
            )
        return adapter
