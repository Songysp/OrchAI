"""Agent provider abstractions and adapters."""

from packages.agents.base import AgentAdapter, AgentSelection, AgentTurnRequest, AgentTurnResult
from packages.agents.claude_adapter import ClaudeAdapter
from packages.agents.codex_adapter import CodexAdapter
from packages.agents.factory import AgentFactory
from packages.agents.gemini_adapter import GeminiAdapter

__all__ = [
    "AgentAdapter",
    "AgentFactory",
    "AgentSelection",
    "AgentTurnRequest",
    "AgentTurnResult",
    "ClaudeAdapter",
    "CodexAdapter",
    "GeminiAdapter",
]
