from __future__ import annotations

import asyncio
import json
import os
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from packages.agents.drivers.base import BaseDriver


class CodexAPIDriver(BaseDriver):
    """OpenAI Responses API driver for coding-oriented models."""

    def __init__(self, api_key: str | None = None, timeout: int = 120):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.timeout = timeout

    async def prompt(self, text: str, model: str | None = None, **kwargs: Any) -> str:
        if not self.api_key:
            raise RuntimeError("OpenAI API key is missing.")

        payload = {
            "model": model or "gpt-5",
            "input": text,
        }
        response = await asyncio.to_thread(self._post_json, payload)
        output_text = response.get("output_text")
        if output_text:
            return str(output_text).strip()

        for item in response.get("output", []):
            for content in item.get("content", []):
                text_value = content.get("text")
                if text_value:
                    return str(text_value).strip()
        raise RuntimeError("OpenAI Responses API returned no text output.")

    def _post_json(self, payload: dict[str, Any]) -> dict[str, Any]:
        request = Request(
            "https://api.openai.com/v1/responses",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace").strip()
            raise RuntimeError(f"OpenAI Responses API call failed ({exc.code}): {body}") from exc
        except URLError as exc:
            raise RuntimeError(f"OpenAI Responses API request failed: {exc.reason}") from exc
