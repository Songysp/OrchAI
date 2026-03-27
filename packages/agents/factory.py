from __future__ import annotations

from packages.agents.base import AgentAdapter, AgentSelection
from packages.domain.models import Project


class AgentFactory:
    def __init__(self, adapters_by_provider: dict[str, AgentAdapter]) -> None:
        self.adapters_by_provider = adapters_by_provider

    def get_agent(self, role: str, project: Project) -> tuple[AgentAdapter, AgentSelection]:
        mapping = project.agent_mapping.get(role)
        if mapping is None:
            raise ValueError(f"Project '{project.project_id}' does not define an agent mapping for role '{role}'.")

        adapter = self.adapters_by_provider.get(mapping.provider)
        if adapter is None:
            raise ValueError(
                f"Provider '{mapping.provider}' for role '{role}' is not registered for project '{project.project_id}'."
            )

        selection = AgentSelection(
            role=role,
            provider=mapping.provider,
            model=mapping.model,
            parameters=mapping.parameters,
        )
        return adapter, selection
