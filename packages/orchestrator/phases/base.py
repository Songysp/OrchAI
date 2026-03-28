from abc import ABC, abstractmethod
from packages.agents.base import AgentAdapter, AgentTurnRequest, AgentTurnResult, AgentSelection
from packages.domain.models.project import Project

class Phase(ABC):
    """Base class for an orchestration phase with standardized prompt handling."""
    
    def __init__(self, adapter: AgentAdapter, role: str):
        self.adapter = adapter
        self.role = role
        self.system_prompt = f"You are the {role.upper()} for OrchAI. Follow CLI-First rules."

    @abstractmethod
    async def execute(self, prompt: str, project: Project, context: dict) -> AgentTurnResult:
        """Executes phase-specific logic."""
        pass

    def _build_request(self, user_content: str, project: Project) -> AgentTurnRequest:
        """Combines system prompt + user content, then wraps in AgentTurnRequest."""
        full_prompt = f"{self.system_prompt}\n\n---\n\n{user_content}"
        selection = AgentSelection(
            role=self.role,
            provider=self.adapter.provider_name,
            model=None,
            parameters={}
        )
        return AgentTurnRequest(
            project=project,
            role=self.role,
            prompt=full_prompt,
            agent_selection=selection
        )
