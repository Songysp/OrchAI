import os
import asyncio
from typing import Any, Optional
from packages.agents.drivers.base import BaseDriver

class ClaudeAPIDriver(BaseDriver):
    """Anthropic API SDK를 사용하는 정식 API 드라이버"""

    def __init__(self, api_key: str | None = None):
        # API 키가 명시되지 않으면 환경변수(ANTHROPIC_API_KEY)에서 가져옵니다.
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self._client = None # Initialize as None

    async def prompt(self, text: str, model: str | None = None, **kwargs: Any) -> str:
        # Lazy import to avoid dependency on 'anthropic' for CLI users
        try:
            from anthropic import AsyncAnthropic
        except ImportError:
            raise RuntimeError(
                "Anthropic SDK ('anthropic' package) is required for API mode. "
                "Please run 'pip install anthropic' or use CLI mode."
            )

        if not self._client:
            if not self.api_key:
                raise RuntimeError("Anthropic API Key is missing.")
            self._client = AsyncAnthropic(api_key=self.api_key)
        
        # 기본 모델 설정
        target_model = model or "claude-3-5-sonnet-20241022"
        
        try:
            message = await self.client.messages.create(
                max_tokens=4096,
                messages=[
                    {
                        "role": "user",
                        "content": text,
                    }
                ],
                model=target_model,
            )
            # 응답 텍스트 추출 (첫 번째 콘텐츠 블록)
            return "".join([block.text for block in message.content if hasattr(block, "text")])
            
        except Exception as e:
            raise RuntimeError(f"Anthropic API call failed: {str(e)}")
