from __future__ import annotations

import pytest

from packages.agents.drivers.codex_cli import CodexCLIDriver
from packages.agents.drivers.gemini_cli import GeminiCLIDriver
from packages.agents.errors import ProviderRateLimitError


def test_gemini_cli_driver_detects_rate_limit() -> None:
    with pytest.raises(ProviderRateLimitError):
        GeminiCLIDriver._raise_for_known_error("rate limit exceeded (429)", 1)


def test_codex_cli_driver_detects_rate_limit() -> None:
    with pytest.raises(ProviderRateLimitError):
        CodexCLIDriver._raise_for_known_error("quota exceeded 429", 1)
