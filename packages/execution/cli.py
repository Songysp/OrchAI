from __future__ import annotations

import asyncio
from pathlib import Path

from packages.domain.models import ExecutionBackend
from packages.execution.base import ExecutionAdapter, ExecutionRequest, ExecutionResult


class CliExecutionAdapter(ExecutionAdapter):
    backend_name = ExecutionBackend.CLI

    async def run(self, request: ExecutionRequest) -> ExecutionResult:
        timeout_seconds = self._timeout_seconds(request)
        workspace = Path(request.project.workspace_path)
        command = request.command.strip()
        if not command:
            return ExecutionResult(
                backend=self.backend_name,
                status="failed",
                summary="CLI execution failed: command is empty.",
                metadata={"workspace_path": str(workspace), "exit_code": None},
            )

        start = asyncio.get_running_loop().time()
        process = await asyncio.create_subprocess_shell(
            command,
            cwd=str(workspace),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout_seconds)
            timed_out = False
        except asyncio.TimeoutError:
            process.kill()
            stdout, stderr = await process.communicate()
            timed_out = True

        elapsed_seconds = round(asyncio.get_running_loop().time() - start, 3)
        exit_code = process.returncode
        stdout_text = stdout.decode("utf-8", errors="replace").strip()
        stderr_text = stderr.decode("utf-8", errors="replace").strip()
        logs = [line for line in [stdout_text, stderr_text] if line]

        if timed_out:
            status = "timeout"
            summary = (
                f"CLI execution timed out after {timeout_seconds} seconds for command: {command}"
            )
        elif exit_code == 0:
            status = "completed"
            summary = f"CLI execution completed successfully for command: {command}"
        else:
            status = "failed"
            summary = f"CLI execution failed with exit code {exit_code} for command: {command}"

        return ExecutionResult(
            backend=self.backend_name,
            status=status,
            summary=summary,
            logs=logs,
            metadata={
                "command": command,
                "workspace_path": str(workspace),
                "exit_code": exit_code,
                "elapsed_seconds": elapsed_seconds,
                "timeout_seconds": timeout_seconds,
                "timed_out": timed_out,
            },
        )

    def _timeout_seconds(self, request: ExecutionRequest) -> float:
        timeout_value = request.metadata.get("timeout_seconds")
        if isinstance(timeout_value, (int, float)) and timeout_value > 0:
            return float(timeout_value)
        return 300.0
