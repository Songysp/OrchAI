from __future__ import annotations

from abc import ABC, abstractmethod

from packages.domain.models import ApprovalRequest, ConversationThread, Decision, Project, Task


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
    def list_tasks(self, project_id: str | None = None) -> list[Task]:
        raise NotImplementedError

    @abstractmethod
    def get_task(self, task_id: str) -> Task | None:
        raise NotImplementedError

    @abstractmethod
    def upsert_task(self, task: Task) -> Task:
        raise NotImplementedError


class ConversationStore(ABC):
    @abstractmethod
    def list_conversations(self, project_id: str | None = None) -> list[ConversationThread]:
        raise NotImplementedError

    @abstractmethod
    def upsert_conversation(self, conversation: ConversationThread) -> ConversationThread:
        raise NotImplementedError


class DecisionStore(ABC):
    @abstractmethod
    def list_decisions(self, project_id: str | None = None) -> list[Decision]:
        raise NotImplementedError

    @abstractmethod
    def upsert_decision(self, decision: Decision) -> Decision:
        raise NotImplementedError


class ApprovalStore(ABC):
    @abstractmethod
    def list_approvals(self, project_id: str | None = None) -> list[ApprovalRequest]:
        raise NotImplementedError

    @abstractmethod
    def get_approval(self, approval_id: str) -> ApprovalRequest | None:
        raise NotImplementedError

    @abstractmethod
    def upsert_approval(self, approval: ApprovalRequest) -> ApprovalRequest:
        raise NotImplementedError
