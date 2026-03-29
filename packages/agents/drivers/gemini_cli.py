from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Any

from packages.agents.drivers.base import BaseDriver
from packages.agents.errors import ProviderCLIError, ProviderRateLimitError

try:
    from subprocess import CREATE_NO_WINDOW
except ImportError:
    CREATE_NO_WINDOW = 0


class GeminiCLIDriver(BaseDriver):
    """Hidden subprocess driver for the locally installed Gemini CLI."""

    def __init__(self, timeout: int = 120, command: str = "gemini"):
        self.timeout = timeout
        self.command = command

    async def prompt(self, text: str, model: str | None = None, **kwargs: Any) -> str:
        gemini_path = os.environ.get("GEMINI_CLI_PATH", r"C:\Users\song\AppData\Roaming\npm\gemini.cmd")
        cwd = kwargs.get("cwd")
        cmd = ["cmd", "/c", gemini_path, "--prompt", text, "--output-format", "text"]
        if model:
            cmd.extend(["--model", model])

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
            raise ProviderCLIError("gemini", f"Gemini CLI request timed out after {self.timeout} seconds.", mode="cli") from exc

        output = stdout.decode(errors="replace").strip()
        error_output = stderr.decode(errors="replace").strip()
        if process.returncode != 0:
            message = error_output or output or f"Gemini CLI exited with code {process.returncode}."
            self._raise_for_known_error(message, process.returncode)
            raise ProviderCLIError("gemini", f"Gemini CLI error (code {process.returncode}): {message}", mode="cli")
        if not output:
            raise ProviderCLIError("gemini", "Gemini CLI returned no text output.", mode="cli")
        return output

    @staticmethod
    def _raise_for_known_error(message: str, returncode: int) -> None:
        normalized = message.lower()
        if "rate limit" in normalized or "quota" in normalized or "429" in normalized:
            raise ProviderRateLimitError(
                "gemini",
                f"Gemini CLI rate limit reached (code {returncode}): {message}",
                status_code=429 if "429" in normalized else None,
                mode="cli",
            )
