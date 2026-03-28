from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseDriver(ABC):
    """AI 엔진과 통신하는 기본 드라이버 규격"""

    @abstractmethod
    async def prompt(self, text: str, model: str | None = None, **kwargs: Any) -> str:
        """프롬프트를 보내고 응답을 문자열로 반환"""
        raise NotImplementedError
