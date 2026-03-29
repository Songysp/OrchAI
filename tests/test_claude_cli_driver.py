from __future__ import annotations

import pytest

from packages.agents.drivers.claude_cli import ClaudeCLIDriver, ClaudeCLIQuotaError


def test_claude_cli_driver_detects_quota_error() -> None:
    with pytest.raises(ClaudeCLIQuotaError) as exc_info:
        ClaudeCLIDriver._raise_for_known_error(
            "You've hit your limit · resets 7pm (Asia/Seoul)",
            1,
        )

    assert "Claude CLI error (code 1)" in str(exc_info.value)
    assert exc_info.value.reset_at == "7pm (Asia/Seoul)"


def test_claude_cli_driver_ignores_generic_errors() -> None:
    ClaudeCLIDriver._raise_for_known_error("Network unavailable", 1)
