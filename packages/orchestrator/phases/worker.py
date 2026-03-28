from packages.agents.base import AgentTurnResult, AgentAdapter
from packages.domain.models.project import Project
from .base import Phase

class WorkerPhase(Phase):
    """Worker phase: Implements the code/logic based on the plan."""
    
    def __init__(self, adapter: AgentAdapter):
        super().__init__(adapter, role="worker")
        self.system_prompt = (
            "You are the OrchAI WORKER. [CONCEPT CHECK] CLI-First, Hybrid Driver, No-Infra.\n"
            "Implement the requested logic using only local assets. Prefer Typer and Rich for CLI/UI."
        )

    async def execute(self, prompt: str, project: Project, context: dict) -> AgentTurnResult:
        plan = context.get("plan", "No plan available")
        history = context.get("history", [])
        combined_context = f"Plan: {plan}\nRecent History: {history[-1] if history else 'None'}"
        request = self._build_request(f"Context:\n{combined_context}\n\nTask: {prompt}", project)
        return await self.adapter.run_turn(request)
