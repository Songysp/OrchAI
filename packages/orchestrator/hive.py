from __future__ import annotations
import logging
from typing import AsyncGenerator, List
from datetime import datetime
import typer

from packages.agents.base import AgentAdapter
from packages.domain.models.project import Project
from packages.domain.models.turn import TurnResult
from packages.orchestrator.loop_state import LoopState, PhaseResult
from packages.orchestrator.phases.planner import PlannerPhase
from packages.orchestrator.phases.worker import WorkerPhase
from packages.orchestrator.phases.refiner import RefinerPhase

logger = logging.getLogger(__name__)

# Phase label shown in CLI status spinner
_PHASE_LABELS = {
    "planner": "Planner is analyzing the task...",
    "worker": "Worker is implementing...",
    "refiner": "Refiner is reviewing...",
    "architect": "Awaiting human intervention...",
}


class HiveOrchestrator:
    """
    Core engine implementing the Planner → Worker → Refiner (PWR) loop.
    [CONCEPT CHECK] CLI-First, Hybrid Driver, No-Infra.

    - execute_stream(): async generator, yields TurnResult per phase (use for real-time UI)
    - execute(): convenience wrapper returning the full history list
    """

    def __init__(self, adapter: AgentAdapter, max_turns: int = 5):
        self.adapter = adapter
        self.max_turns = max_turns
        self.planner = PlannerPhase(adapter)
        self.worker = WorkerPhase(adapter)
        self.refiner = RefinerPhase(adapter)

    async def execute_stream(
        self, prompt: str, project: Project
    ) -> AsyncGenerator[TurnResult, None]:
        """
        Streams each TurnResult as it is produced.
        Callers can react to each turn immediately (e.g., render to CLI).
        """
        state = LoopState(max_turns=self.max_turns)
        run_id = f"run_{int(datetime.now().timestamp())}"
        turn_index = 0

        # ── Phase 1: Planning ──────────────────────────────────────────────
        logger.info("[HIVE] Phase 1: Planner")
        plan_result = await self.planner.execute(prompt, project, {})
        plan_persist = TurnResult(
            turn_id=f"{run_id}_p0",
            run_id=run_id,
            turn_index=turn_index,
            role="planner",
            prompt=prompt,
            output=plan_result.output,
            finished_at=datetime.now(),
        )
        state.add_phase_result(PhaseResult(role="planner", turn_number=0, output=plan_result.output))
        yield plan_persist

        # ── Phase 2–3: Worker / Refiner ping-pong loop ────────────────────
        current_prompt = prompt
        while not state.is_complete:
            if state.is_max_turns_exceeded():
                logger.warning("[HIVE] Max turns reached — escalating to human (T6).")
                intervention = typer.prompt(
                    "\n[HiveMind] Max turns reached.\n"
                    "Enter 'DONE' to finish, or provide feedback to continue",
                    default="DONE",
                )

                if intervention.strip().upper() == "DONE":
                    state.mark_complete()
                    break

                # Human feedback → yield escalation record then resume loop
                turn_index += 1
                escalation_record = TurnResult(
                    turn_id=f"{run_id}_esc_{state.turn_count}",
                    run_id=run_id,
                    turn_index=turn_index,
                    role="architect",
                    prompt="Escalation triggered — human intervention requested.",
                    output=intervention,
                    status="escalated",
                    escalation_context=intervention,
                    finished_at=datetime.now(),
                )
                yield escalation_record
                current_prompt = f"Human Intervention: {intervention}"
                state.max_turns += 3
                logger.info(f"[HIVE] Resuming with human feedback. Extended max_turns → {state.max_turns}")
                continue

            state.turn_count += 1
            idx = state.turn_count

            # Worker turn
            logger.info(f"[HIVE] Turn {idx}: Worker")
            turn_index += 1
            worker_result = await self.worker.execute(
                prompt=current_prompt,
                project=project,
                context={
                    "plan": plan_result.output,
                    "turn": idx,
                },
            )
            worker_persist = TurnResult(
                turn_id=f"{run_id}_w{idx}",
                run_id=run_id,
                turn_index=turn_index,
                role="worker",
                prompt=current_prompt,
                output=worker_result.output,
                finished_at=datetime.now(),
            )
            state.add_phase_result(PhaseResult(role="worker", turn_number=idx, output=worker_result.output))
            yield worker_persist

            # Refiner turn
            logger.info(f"[HIVE] Turn {idx}: Refiner")
            turn_index += 1
            refiner_result = await self.refiner.execute(
                prompt=worker_result.output,
                project=project,
                context={"plan": plan_result.output},
            )
            refiner_persist = TurnResult(
                turn_id=f"{run_id}_r{idx}",
                run_id=run_id,
                turn_index=turn_index,
                role="refiner",
                prompt=worker_result.output,
                output=refiner_result.output,
                finished_at=datetime.now(),
            )
            state.add_phase_result(PhaseResult(role="refiner", turn_number=idx, output=refiner_result.output))
            yield refiner_persist

            if refiner_result.output.strip().upper().startswith("DONE"):
                state.mark_complete()
                logger.info("[HIVE] Refiner confirmed completion. Loop closed.")

    async def execute(self, prompt: str, project: Project) -> List[TurnResult]:
        """Convenience wrapper — collects the full stream and returns it as a list."""
        return [turn async for turn in self.execute_stream(prompt, project)]
