from __future__ import annotations

from packages.domain.models import ExecutionBackend
from packages.execution.base import ExecutionAdapter, ExecutionRequest, ExecutionResult


class CliExecutionAdapter(ExecutionAdapter):
    backend_name = ExecutionBackend.CLI

    async def run(self, request: ExecutionRequest) -> ExecutionResult:
        return ExecutionResult(
            backend=self.backend_name,
            status="stub",
            summary=f"CLI execution adapter skeleton for command: {request.command}",
        )
