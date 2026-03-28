import asyncio
import os
from typing import Any

from packages.agents.drivers.base import BaseDriver


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

        try:
            # Execute subprocess with FULL ENVIRONMENT inheritance
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                # On Windows, we need to ensure the environment is inherited correctly
                env=os.environ.copy()
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=self.timeout)
                
                if process.returncode != 0:
                    error_msg = stderr.decode(errors="replace").strip()
                    if not error_msg:
                        error_msg = stdout.decode(errors="replace").strip()
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
