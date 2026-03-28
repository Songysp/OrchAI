from __future__ import annotations

from typing import Any

from packages.agents.drivers.base import BaseDriver


class ClaudeAPIDriver(BaseDriver):
    """Anthropic API SDK를 사용하는 정식 API 드라이버 (Future)"""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key
        # TODO: self.client = anthropic.Anthropic(api_key=api_key)

    async def prompt(self, text: str, model: str | None = None, **kwargs: Any) -> str:
        # TODO: 실제 API 호출 로직 구현
        # 현재는 안내 메시지만 출력
        raise NotImplementedError(
            "ClaudeAPIDriver is not fully implemented yet. Please use 'cli' method for now."
        )
