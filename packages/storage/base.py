from __future__ import annotations

from abc import ABC, abstractmethod

from packages.domain.models import Approval, Decision, Project, Task


class ProjectStore(ABC):
    @abstractmethod
    def list_projects(self) -> list[Project]:
        raise NotImplementedError

    @abstractmethod
    def get_project(self, project_id: str) -> Project | None:
        raise NotImplementedError

    @abstractmethod
    def upsert_project(self, project: Project) -> Project:
        raise NotImplementedError


class TaskStore(ABC):
    @abstractmethod
    def list_tasks(self, project_id: str) -> list[Task]:
        raise NotImplementedError

    @abstractmethod
    def get_task(self, project_id: str, task_id: str) -> Task | None:
        raise NotImplementedError

    @abstractmethod
    def upsert_task(self, task: Task) -> Task:
        raise NotImplementedError


class DecisionStore(ABC):
    @abstractmethod
    def list_decisions(self, project_id: str, task_id: str | None = None) -> list[Decision]:
        raise NotImplementedError

    @abstractmethod
    def get_decision(self, project_id: str, decision_id: str) -> Decision | None:
        raise NotImplementedError

    @abstractmethod
    def upsert_decision(self, decision: Decision) -> Decision:
        raise NotImplementedError


class ApprovalStore(ABC):
    @abstractmethod
    def list_approvals(self, project_id: str, task_id: str | None = None) -> list[Approval]:
        raise NotImplementedError

    @abstractmethod
    def get_approval(self, project_id: str, approval_id: str) -> Approval | None:
        raise NotImplementedError

    @abstractmethod
    def upsert_approval(self, approval: Approval) -> Approval:
        raise NotImplementedError
