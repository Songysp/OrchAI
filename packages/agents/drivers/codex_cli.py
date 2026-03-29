from __future__ import annotations

import asyncio
import os
import tempfile
from pathlib import Path
from typing import Any

from packages.agents.drivers.base import BaseDriver
from packages.agents.errors import ProviderCLIError, ProviderRateLimitError

try:
    from subprocess import CREATE_NO_WINDOW
except ImportError:
    CREATE_NO_WINDOW = 0


class CodexCLIDriver(BaseDriver):
    """Hidden subprocess driver for the locally installed Codex CLI."""

    def __init__(self, timeout: int = 120, command: str = "codex"):
        self.timeout = timeout
        self.command = command

    async def prompt(self, text: str, model: str | None = None, **kwargs: Any) -> str:
        codex_path = os.environ.get("CODEX_CLI_PATH", r"C:\Users\song\AppData\Roaming\npm\codex.cmd")
        cwd = kwargs.get("cwd")
        with tempfile.NamedTemporaryFile("w+", encoding="utf-8", delete=False, suffix=".txt") as handle:
            output_path = handle.name

        cmd = [
            "cmd",
            "/c",
            codex_path,
            "exec",
            "--skip-git-repo-check",
            "--color",
            "never",
            "--output-last-message",
            output_path,
        ]
        if model:
            cmd.extend(["--model", model])
        if cwd:
            cmd.extend(["--cd", str(Path(cwd))])
        cmd.append(text)

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=os.environ.copy(),
            cwd=str(Path(cwd)) if cwd else None,
            creationflags=CREATE_NO_WINDOW if os.name == "nt" else 0,
        )

        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=self.timeout)
        except asyncio.TimeoutError as exc:
            process.kill()
            await process.wait()
            raise ProviderCLIError("codex", f"Codex CLI request timed out after {self.timeout} seconds.", mode="cli") from exc
        finally:
            stdout_text = stdout.decode(errors="replace").strip() if "stdout" in locals() else ""
            stderr_text = stderr.decode(errors="replace").strip() if "stderr" in locals() else ""

        try:
            output = Path(output_path).read_text(encoding="utf-8").strip() if Path(output_path).exists() else ""
        finally:
            if Path(output_path).exists():
                Path(output_path).unlink(missing_ok=True)

        if process.returncode != 0:
            message = stderr_text or stdout_text or f"Codex CLI exited with code {process.returncode}."
            self._raise_for_known_error(message, process.returncode)
            raise ProviderCLIError("codex", f"Codex CLI error (code {process.returncode}): {message}", mode="cli")
        if not output:
            raise ProviderCLIError("codex", "Codex CLI returned no text output.", mode="cli")
        return output

    @staticmethod
    def _raise_for_known_error(message: str, returncode: int) -> None:
        normalized = message.lower()
        if "rate limit" in normalized or "quota" in normalized or "429" in normalized:
            raise ProviderRateLimitError(
                "codex",
                f"Codex CLI rate limit reached (code {returncode}): {message}",
                status_code=429 if "429" in normalized else None,
                mode="cli",
            )
