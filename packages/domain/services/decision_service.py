from __future__ import annotations

from packages.domain.models import Decision
from packages.storage.base import DecisionStore


class DecisionService:
    def __init__(self, decision_store: DecisionStore) -> None:
        self.decision_store = decision_store

    def record(self, decision: Decision) -> Decision:
        return self.decision_store.upsert_decision(decision)

    def list_for_task(self, project_id: str, task_id: str) -> list[Decision]:
        return self.decision_store.list_decisions(project_id, task_id=task_id)
