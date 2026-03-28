from packages.agents.base import AgentTurnResult, AgentAdapter
from packages.domain.models.project import Project
from .base import Phase

class PlannerPhase(Phase):
    """Planner phase: Analyzes request and creates a physical file-structure plan."""
    
    def __init__(self, adapter: AgentAdapter):
        super().__init__(adapter, role="planner")
        self.system_prompt = (
            "You are the OrchAI PLANNER. [CONCEPT CHECK] CLI-First, Hybrid Driver, No-Infra.\n"
            "Your task is to analyze the user request and propose a physical file structure and execution plan.\n"
            "Focus on local stdlib-first solutions."
        )

    async def execute(self, prompt: str, project: Project, context: dict) -> AgentTurnResult:
        request = self._build_request(prompt, project)
        return await self.adapter.run_turn(request)
