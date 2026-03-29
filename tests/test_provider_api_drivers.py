from __future__ import annotations

import pytest

from packages.agents.drivers.codex_api import CodexAPIDriver
from packages.agents.drivers.gemini_api import GeminiAPIDriver


@pytest.mark.anyio
async def test_gemini_api_driver_extracts_text(monkeypatch: pytest.MonkeyPatch) -> None:
    driver = GeminiAPIDriver(api_key="gemini-key")

    monkeypatch.setattr(
        driver,
        "_post_json",
        lambda model, payload: {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {"text": "hello "},
                            {"text": "gemini"},
                        ]
                    }
                }
            ]
        },
    )

    output = await driver.prompt("hi", model="gemini-2.0-flash")

    assert output == "hello gemini"


@pytest.mark.anyio
async def test_codex_api_driver_prefers_output_text(monkeypatch: pytest.MonkeyPatch) -> None:
    driver = CodexAPIDriver(api_key="openai-key")
    monkeypatch.setattr(driver, "_post_json", lambda payload: {"output_text": "hello codex"})

    output = await driver.prompt("hi", model="gpt-5")

    assert output == "hello codex"
