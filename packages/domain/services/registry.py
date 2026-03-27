from __future__ import annotations

from pathlib import Path

from packages.agents.base import AgentAdapter
from packages.agents.claude_adapter import ClaudeAdapter
from packages.agents.codex_adapter import CodexAdapter
from packages.agents.gemini_adapter import GeminiAdapter
from packages.chat.base import ChatAdapter
from packages.chat.discord_adapter import DiscordAdapter
from packages.chat.slack_adapter import SlackAdapter
from packages.config.loader import ConfigLoader
from packages.config.models import LoadedConfig
from packages.rules import SimpleRulesEngine
from packages.storage.base import ApprovalStore, DecisionStore, ProjectStore, TaskStore
from packages.storage.file_store import (
    FileApprovalStore,
    FileDecisionStore,
    FileProjectStore,
    FileTaskStore,
)


class PlatformRegistry:
    def __init__(self, root_path: Path) -> None:
        self.root_path = root_path
        self.loaded_config: LoadedConfig = ConfigLoader(root_path).load()
        data_path = root_path / self.loaded_config.platform.paths.data_dir

        self.project_store: ProjectStore = FileProjectStore(data_path)
        self.task_store: TaskStore = FileTaskStore(data_path)
        self.decision_store: DecisionStore = FileDecisionStore(data_path)
        self.approval_store: ApprovalStore = FileApprovalStore(data_path)

        self.agent_adapters: dict[str, AgentAdapter] = {
            "claude": ClaudeAdapter(),
            "gemini": GeminiAdapter(),
            "codex": CodexAdapter(),
        }
        self.chat_adapters: dict[str, ChatAdapter] = {
            "slack": SlackAdapter(),
            "discord": DiscordAdapter(),
        }
        self.rules_engine = SimpleRulesEngine()

        self._seed_projects()

    def _seed_projects(self) -> None:
        for project in self.loaded_config.projects:
            self.project_store.upsert_project(project)
