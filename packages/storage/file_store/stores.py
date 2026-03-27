from __future__ import annotations

from pathlib import Path

from packages.domain.models import ApprovalRequest, ConversationThread, Decision, Project, Task
from packages.storage.base import ApprovalStore, ConversationStore, DecisionStore, ProjectStore, TaskStore
from packages.storage.file_store.json_store import JsonCollectionStore


class FileProjectStore(ProjectStore):
    def __init__(self, root_path: Path) -> None:
        self._store = JsonCollectionStore(root_path, "projects", Project, "project_id")

    def list_projects(self) -> list[Project]:
        return self._store.list()

    def get_project(self, project_id: str) -> Project | None:
        return self._store.get(project_id)

    def upsert_project(self, project: Project) -> Project:
        return self._store.upsert(project)


class FileTaskStore(TaskStore):
    def __init__(self, root_path: Path) -> None:
        self._store = JsonCollectionStore(root_path, "tasks", Task, "task_id")

    def list_tasks(self, project_id: str | None = None) -> list[Task]:
        tasks = self._store.list()
        if project_id is None:
            return tasks
        return [task for task in tasks if task.project_id == project_id]

    def get_task(self, task_id: str) -> Task | None:
        return self._store.get(task_id)

    def upsert_task(self, task: Task) -> Task:
        return self._store.upsert(task)


class FileConversationStore(ConversationStore):
    def __init__(self, root_path: Path) -> None:
        self._store = JsonCollectionStore(root_path, "conversations", ConversationThread, "conversation_id")

    def list_conversations(self, project_id: str | None = None) -> list[ConversationThread]:
        conversations = self._store.list()
        if project_id is None:
            return conversations
        return [item for item in conversations if item.project_id == project_id]

    def upsert_conversation(self, conversation: ConversationThread) -> ConversationThread:
        return self._store.upsert(conversation)


class FileDecisionStore(DecisionStore):
    def __init__(self, root_path: Path) -> None:
        self._store = JsonCollectionStore(root_path, "decisions", Decision, "decision_id")

    def list_decisions(self, project_id: str | None = None) -> list[Decision]:
        decisions = self._store.list()
        if project_id is None:
            return decisions
        return [item for item in decisions if item.project_id == project_id]

    def upsert_decision(self, decision: Decision) -> Decision:
        return self._store.upsert(decision)


class FileApprovalStore(ApprovalStore):
    def __init__(self, root_path: Path) -> None:
        self._store = JsonCollectionStore(root_path, "approvals", ApprovalRequest, "approval_id")

    def list_approvals(self, project_id: str | None = None) -> list[ApprovalRequest]:
        approvals = self._store.list()
        if project_id is None:
            return approvals
        return [item for item in approvals if item.project_id == project_id]

    def get_approval(self, approval_id: str) -> ApprovalRequest | None:
        return self._store.get(approval_id)

    def upsert_approval(self, approval: ApprovalRequest) -> ApprovalRequest:
        return self._store.upsert(approval)
