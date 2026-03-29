from __future__ import annotations

import asyncio
import json
import os
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from packages.agents.drivers.base import BaseDriver
from packages.agents.errors import ProviderAPIError, ProviderRateLimitError


class GeminiAPIDriver(BaseDriver):
    """Google Gemini API driver using direct HTTPS requests."""

    def __init__(self, api_key: str | None = None, timeout: int = 120):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.timeout = timeout

    async def prompt(self, text: str, model: str | None = None, **kwargs: Any) -> str:
        if not self.api_key:
            raise RuntimeError("Gemini API key is missing.")

        target_model = model or "gemini-2.0-flash"
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": text,
                        }
                    ]
                }
            ]
        }

        response = await asyncio.to_thread(self._post_json, target_model, payload)
        parts = response.get("candidates", [{}])[0].get("content", {}).get("parts", [])
        text_parts = [part.get("text", "") for part in parts if part.get("text")]
        if not text_parts:
            raise RuntimeError("Gemini API returned no text output.")
        return "".join(text_parts).strip()

    def _post_json(self, model: str, payload: dict[str, Any]) -> dict[str, Any]:
        endpoint = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{quote(model)}:generateContent?key={quote(self.api_key)}"
        )
        request = Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace").strip()
            if exc.code == 429:
                raise ProviderRateLimitError(
                    "gemini",
                    f"Gemini API rate limit reached ({exc.code}): {body}",
                    status_code=exc.code,
                ) from exc
            raise ProviderAPIError(
                "gemini",
                f"Gemini API call failed ({exc.code}): {body}",
                status_code=exc.code,
            ) from exc
        except URLError as exc:
            raise ProviderAPIError("gemini", f"Gemini API request failed: {exc.reason}") from exc
