from packages.agents.base import AgentTurnResult, AgentAdapter
from packages.domain.models.project import Project
from .base import Phase

class RefinerPhase(Phase):
    """Refiner phase: Reviews worker output and decides whether to REPEAT or DONE."""
    
    def __init__(self, adapter: AgentAdapter):
        super().__init__(adapter, role="refiner")
        self.system_prompt = (
            "You are the OrchAI REFINER. [CONCEPT CHECK] CLI-First, Hybrid Driver, No-Infra.\n"
            "Review the worker output. If it is complete, start your response with 'DONE'.\n"
            "If incomplete or poor quality, provide detailed correction feedback."
        )

    async def execute(self, prompt: str, project: Project, context: dict) -> AgentTurnResult:
        plan = context.get("plan", "No plan provided")
        request = self._build_request(f"Plan: {plan}\nWorker Output to Review: {prompt}", project)
        return await self.adapter.run_turn(request)
