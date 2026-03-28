"""Execution backends for local CLI and hosted automation."""

from packages.execution.base import ExecutionAdapter, ExecutionRequest, ExecutionResult
from packages.execution.cli import CliExecutionAdapter
from packages.execution.github_actions import GitHubActionsExecutionAdapter

__all__ = [
    "ExecutionAdapter",
    "ExecutionRequest",
    "ExecutionResult",
    "CliExecutionAdapter",
    "GitHubActionsExecutionAdapter",
]
