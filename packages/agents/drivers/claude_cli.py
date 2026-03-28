from __future__ import annotations

import asyncio
from typing import Any

from packages.agents.drivers.base import BaseDriver


class ClaudeCLIDriver(BaseDriver):
    """로컬 터미널의 'claude' CLI를 사용하는 드라이버"""

    def __init__(self, timeout: int = 120):
        self.timeout = timeout

    async def prompt(self, text: str, model: str | None = None, **kwargs: Any) -> str:
        # claude --print "질문" 명령어를 위해 리스트 구성
        cmd = ["claude"]
        
        # 모델 지정이 있을 경우 추가 (예: claude --model claude-3-5-sonnet-20241022 --print "...")
        if model:
            cmd.extend(["--model", model])
            
        cmd.extend(["--print", text])

        try:
            # 비동기적으로 subprocess 실행
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=self.timeout)
            
            if process.returncode != 0:
                error_msg = stderr.decode().strip()
                raise RuntimeError(f"Claude CLI error (code {process.returncode}): {error_msg}")
            
            return stdout.decode().strip()
            
        except asyncio.TimeoutError:
            raise RuntimeError(f"Claude CLI request timed out after {self.timeout} seconds.")
        except Exception as e:
            raise RuntimeError(f"Failed to execute Claude CLI: {str(e)}")
