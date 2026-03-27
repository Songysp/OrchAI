from __future__ import annotations

from packages.agents import AgentAdapter, AgentFactory, AgentSelection
from packages.chat.base import ChatAdapter
from packages.domain.models import Project
from packages.domain.services.registry import PlatformRegistry


class ProjectRuntime:
    def __init__(self, registry: PlatformRegistry) -> None:
        self.registry = registry
        self.agent_factory = AgentFactory(registry.agent_adapters)

    def get_project(self, project_id: str) -> Project:
        project = self.registry.project_store.get_project(project_id)
        if project is None:
            raise ValueError(f"Project '{project_id}' was not found.")
        return project

    def get_agent(self, project: Project, role: str) -> tuple[AgentAdapter, AgentSelection]:
        return self.agent_factory.get_agent(role=role, project=project)

    def get_chat_adapter(self, project: Project) -> ChatAdapter:
        adapter = self.registry.chat_adapters.get(project.chat_platform)
        if adapter is None:
            raise ValueError(
                f"Chat platform '{project.chat_platform}' is not registered for project '{project.project_id}'."
            )
        return adapter
