from __future__ import annotations

from pydantic import BaseModel, Field

from apps.orchestrator.services.project_runtime import ProjectRuntime
from packages.agents.base import AgentTurnRequest, AgentTurnResult
from packages.chat.base import ChatDelivery
from packages.domain.models import Approval, ApprovalStatus, Decision, Project, Task, TaskStage, TaskStatus
from packages.domain.models.common import utc_now
from packages.domain.services import DecisionService, TaskService
from packages.storage.base import ApprovalStore


class RoleRunResult(BaseModel):
    role: str
    provider: str
    model: str | None = None
    output: str
    metadata: dict[str, object] = Field(default_factory=dict)


class TaskRunResult(BaseModel):
    task_id: str
    project_id: str
    title: str
    final_stage: TaskStage
    final_status: TaskStatus
    representative_summary: str
    decision_id: str
    role_results: list[RoleRunResult]
    chat_deliveries: list[ChatDelivery] = Field(default_factory=list)
    approval_id: str | None = None
    approval_required: bool = False


class RepresentativeWorkflow:
    def __init__(
        self,
        runtime: ProjectRuntime,
        task_service: TaskService,
        decision_service: DecisionService,
        approval_store: ApprovalStore,
    ) -> None:
        self.runtime = runtime
        self.task_service = task_service
        self.decision_service = decision_service
        self.approval_store = approval_store

    async def run(self, task: Task) -> TaskRunResult:
        project = self.runtime.get_project(task.project_id)
        chat_adapter = self.runtime.get_chat_adapter(project)
        role_results: list[RoleRunResult] = []
        chat_deliveries: list[ChatDelivery] = []

        task = self.task_service.transition_task(
            task,
            stage=TaskStage.PLANNING,
            status=TaskStatus.PLANNING,
            summary="Representative is summarizing the request and planner analysis is starting.",
        )
        chat_deliveries.append(
            await chat_adapter.post_ops_log(
                project,
                f"Task {task.task_id} entered planning stage.",
            )
        )
        representative_result = await self._run_role(
            project=project,
            role="representative",
            prompt=self._representative_prompt(task),
            context={"task_id": task.task_id, "user_input": task.description or ""},
        )
        role_results.append(representative_result)
        chat_deliveries.append(
            await chat_adapter.post_user_message(
                project,
                f"Representative summary for task {task.task_id}: {representative_result.output}",
            )
        )

        planner_result = await self._run_role(
            project=project,
            role="planner",
            prompt=self._planner_prompt(task, representative_result.output),
            context={"task_id": task.task_id, "representative_summary": representative_result.output},
        )
        role_results.append(planner_result)
        chat_deliveries.append(
            await chat_adapter.post_council_message(
                project,
                f"Planner analysis for task {task.task_id}: {planner_result.output}",
            )
        )

        task = self.task_service.transition_task(
            task,
            stage=TaskStage.BUILDING,
            status=TaskStatus.IN_PROGRESS,
            summary="Builder is preparing an implementation proposal.",
        )
        chat_deliveries.append(
            await chat_adapter.post_ops_log(
                project,
                f"Task {task.task_id} entered building stage.",
            )
        )
        builder_result = await self._run_role(
            project=project,
            role="builder",
            prompt=self._builder_prompt(task, planner_result.output),
            context={"task_id": task.task_id, "planner_analysis": planner_result.output},
        )
        role_results.append(builder_result)
        chat_deliveries.append(
            await chat_adapter.post_ops_log(
                project,
                f"Builder proposal for task {task.task_id}: {builder_result.output}",
            )
        )

        task = self.task_service.transition_task(
            task,
            stage=TaskStage.REVIEWING,
            status=TaskStatus.REVIEW,
            summary="Critic is reviewing the proposed implementation.",
        )
        chat_deliveries.append(
            await chat_adapter.post_council_message(
                project,
                f"Task {task.task_id} entered reviewing stage.",
            )
        )
        critic_result = await self._run_role(
            project=project,
            role="critic",
            prompt=self._critic_prompt(task, builder_result.output),
            context={"task_id": task.task_id, "builder_output": builder_result.output},
        )
        role_results.append(critic_result)
        chat_deliveries.append(
            await chat_adapter.post_council_message(
                project,
                f"Critic review for task {task.task_id}: {critic_result.output}",
            )
        )

        task = self.task_service.transition_task(
            task,
            stage=TaskStage.TESTING,
            status=TaskStatus.TESTING,
            summary="Tester is identifying validation concerns and checks.",
        )
        chat_deliveries.append(
            await chat_adapter.post_ops_log(
                project,
                f"Task {task.task_id} entered testing stage.",
            )
        )
        tester_result = await self._run_role(
            project=project,
            role="tester",
            prompt=self._tester_prompt(task, builder_result.output, critic_result.output),
            context={
                "task_id": task.task_id,
                "builder_output": builder_result.output,
                "critic_review": critic_result.output,
            },
        )
        role_results.append(tester_result)
        chat_deliveries.append(
            await chat_adapter.post_ops_log(
                project,
                f"Tester concerns for task {task.task_id}: {tester_result.output}",
            )
        )

        final_summary = self._final_summary(task, role_results)
        policy_evaluation = self.runtime.registry.rules_engine.evaluate(
            project=project,
            task=task,
            context={
                "representative": representative_result.output,
                "planner": planner_result.output,
                "builder": builder_result.output,
                "critic": critic_result.output,
                "tester": tester_result.output,
            },
        )
        decision = self.decision_service.record(
            Decision(
                task_id=task.task_id,
                project_id=task.project_id,
                summary=final_summary,
                chosen_option="representative-aggregated-plan",
            )
        )

        approval: Approval | None = None
        approved_approvals = [
            existing
            for existing in self.approval_store.list_approvals(project.project_id, task.task_id)
            if existing.status == ApprovalStatus.APPROVED
        ]
        final_stage = TaskStage.COMPLETED
        final_status = TaskStatus.COMPLETED
        final_status_summary = final_summary

        if policy_evaluation.approval_required and not approved_approvals:
            approval = self.approval_store.upsert_approval(
                Approval(
                    task_id=task.task_id,
                    project_id=task.project_id,
                    comment="; ".join(policy_evaluation.reasons),
                )
            )
            final_stage = TaskStage.WAITING_HUMAN
            final_status = TaskStatus.BLOCKED
            final_status_summary = (
                "Task requires human approval before proceeding. "
                + " ".join(policy_evaluation.reasons)
            )
            chat_deliveries.append(
                await chat_adapter.post_approval_request(
                    project,
                    final_status_summary,
                )
            )
            chat_deliveries.append(
                await chat_adapter.post_ops_log(
                    project,
                    f"Task {task.task_id} is waiting for human approval.",
                )
            )
        else:
            chat_deliveries.append(
                await chat_adapter.post_user_message(
                    project,
                    f"Representative final summary for task {task.task_id}: {final_summary}",
                )
            )

        completed_task = task.model_copy(
            update={
                "stage": final_stage,
                "status": final_status,
                "updated_at": utc_now(),
                "metadata": {
                    **task.metadata,
                    "run": {
                        "representative_summary": representative_result.output,
                        "role_results": [result.model_dump(mode="json") for result in role_results],
                        "decision_id": decision.decision_id,
                        "policy_evaluation": policy_evaluation.model_dump(mode="json"),
                        "approval_id": approval.approval_id if approval is not None else None,
                        "chat_deliveries": [delivery.model_dump(mode="json") for delivery in chat_deliveries],
                    },
                    "status_summary": final_status_summary,
                },
            }
        )
        completed_task = self.task_service.task_store.upsert_task(completed_task)

        return TaskRunResult(
            task_id=completed_task.task_id,
            project_id=completed_task.project_id,
            title=completed_task.title,
            final_stage=completed_task.stage,
            final_status=completed_task.status,
            representative_summary=final_status_summary,
            decision_id=decision.decision_id,
            role_results=role_results,
            chat_deliveries=chat_deliveries,
            approval_id=approval.approval_id if approval is not None else None,
            approval_required=policy_evaluation.approval_required,
        )

    async def _run_role(
        self,
        project: Project,
        role: str,
        prompt: str,
        context: dict[str, object],
    ) -> RoleRunResult:
        adapter, selection = self.runtime.get_agent(project, role)
        result = await adapter.run_turn(
            AgentTurnRequest(
                project=project,
                role=role,
                prompt=prompt,
                agent_selection=selection,
                context=context,
            )
        )
        return RoleRunResult(
            role=result.role,
            provider=result.provider,
            model=result.model,
            output=result.output,
            metadata=result.metadata,
        )

    def _representative_prompt(self, task: Task) -> str:
        return f"Summarize the user's request and frame the implementation goal: {task.description or task.title}"

    def _planner_prompt(self, task: Task, representative_summary: str) -> str:
        return f"Analyze the request, constraints, and likely implementation plan. Representative summary: {representative_summary}"

    def _builder_prompt(self, task: Task, planner_analysis: str) -> str:
        return f"Propose a concrete implementation approach for task '{task.title}'. Planner analysis: {planner_analysis}"

    def _critic_prompt(self, task: Task, builder_output: str) -> str:
        return f"Review the proposed implementation for risks, tradeoffs, and missing concerns. Proposal: {builder_output}"

    def _tester_prompt(self, task: Task, builder_output: str, critic_review: str) -> str:
        return (
            "Propose validation concerns, tests, and likely failure modes. "
            f"Implementation proposal: {builder_output}. Critic review: {critic_review}"
        )

    def _final_summary(self, task: Task, role_results: list[RoleRunResult]) -> str:
        representative = self._output_for(role_results, "representative")
        planner = self._output_for(role_results, "planner")
        builder = self._output_for(role_results, "builder")
        critic = self._output_for(role_results, "critic")
        tester = self._output_for(role_results, "tester")
        return (
            f"Task '{task.title}' was orchestrated through representative, planner, builder, critic, and tester stages. "
            f"Representative summary: {representative} "
            f"Planner analysis: {planner} "
            f"Builder proposal: {builder} "
            f"Critic review: {critic} "
            f"Tester concerns: {tester}"
        )

    def _output_for(self, role_results: list[RoleRunResult], role: str) -> str:
        for result in role_results:
            if result.role == role:
                return result.output
        return ""
