import asyncio
import os
import re
import tempfile
from typing import Any

from packages.agents.drivers.base import BaseDriver


class ClaudeCLIQuotaError(RuntimeError):
    """Raised when the local Claude CLI rejects a request due to usage limits."""

    def __init__(self, message: str, reset_at: str | None = None):
        super().__init__(message)
        self.reset_at = reset_at


class ClaudeCLIDriver(BaseDriver):
    """Driver that uses the local terminal's 'claude' CLI tool."""

    def __init__(self, timeout: int = 120, command: str = "claude"):
        self.timeout = timeout
        self.command = command

    async def prompt(self, text: str, model: str | None = None, **kwargs: Any) -> str:
        # On Windows, executing a .cmd requires 'cmd /c' and full environment inheritance
        # We'll use the path provided in the environment or fallback to standard npm path
        claude_path = os.environ.get("CLAUDE_CLI_PATH", r'C:\Users\song\AppData\Roaming\npm\claude.cmd')

        # Build command list
        cmd = ["cmd", "/c", claude_path]
        if model:
            cmd.extend(["--model", model])
        cmd.extend(["--print", text])

        # Run from a neutral temp directory so project-level CLAUDE.md is not picked up
        neutral_cwd = tempfile.gettempdir()

        try:
            # Execute subprocess with FULL ENVIRONMENT inheritance
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=os.environ.copy(),
                cwd=neutral_cwd,
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=self.timeout)
                
                if process.returncode != 0:
                    error_msg = stderr.decode(errors="replace").strip()
                    if not error_msg:
                        error_msg = stdout.decode(errors="replace").strip()
                    self._raise_for_known_error(error_msg, process.returncode)
                    raise RuntimeError(f"Claude CLI error (code {process.returncode}): {error_msg}")
                
                return stdout.decode(errors="replace").strip()
            except asyncio.TimeoutError:
                try:
                    process.kill()
                    await process.wait()
                except:
                    pass
                raise RuntimeError(f"Claude CLI request timed out after {self.timeout} seconds.")
            finally:
                # Ensure the process is fully reaped before returning
                if process.returncode is None:
                    try:
                        process.terminate()
                        await process.wait()
                    except:
                        pass
        except Exception as e:
            if isinstance(e, RuntimeError):
                raise
            raise RuntimeError(f"Failed to execute Claude CLI: {str(e)}")

    @staticmethod
    def _raise_for_known_error(error_msg: str, returncode: int) -> None:
        normalized = error_msg.lower()
        if "hit your limit" not in normalized:
            return

        match = re.search(r"resets?\s+(.+)$", error_msg, re.IGNORECASE)
        reset_at = match.group(1).strip() if match else None
        raise ClaudeCLIQuotaError(
            f"Claude CLI error (code {returncode}): {error_msg}",
            reset_at=reset_at,
        )
