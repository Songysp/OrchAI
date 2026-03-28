from __future__ import annotations

import io
import sys
from pathlib import Path
from urllib.error import HTTPError

import pytest

from packages.domain.models import Project, Task
from packages.execution import (
    CliExecutionAdapter,
    ExecutionRequest,
    GitHubActionsExecutionAdapter,
)


def _project(workspace_path: Path, repo_url: str = "https://github.com/example/orchai") -> Project:
    return Project(
        project_id="project-exec",
        repo_url=repo_url,
        workspace_path=str(workspace_path),
        chat_platform="slack",
        default_branch="main",
    )


def _task(project_id: str = "project-exec") -> Task:
    return Task(project_id=project_id, title="Run execution adapter")


@pytest.mark.anyio
async def test_cli_execution_adapter_completes_successfully(tmp_path: Path) -> None:
    adapter = CliExecutionAdapter()
    request = ExecutionRequest(
        project=_project(tmp_path),
        task=_task(),
        command=f'"{sys.executable}" -c "print(\'hello from cli\')"',
    )

    result = await adapter.run(request)

    assert result.status == "completed"
    assert "completed successfully" in result.summary
    assert any("hello from cli" in log for log in result.logs)
    assert result.metadata["exit_code"] == 0
    assert result.metadata["workspace_path"] == str(tmp_path)


@pytest.mark.anyio
async def test_cli_execution_adapter_reports_nonzero_exit(tmp_path: Path) -> None:
    adapter = CliExecutionAdapter()
    request = ExecutionRequest(
        project=_project(tmp_path),
        task=_task(),
        command=f'"{sys.executable}" -c "import sys; print(\'boom\'); sys.exit(3)"',
    )

    result = await adapter.run(request)

    assert result.status == "failed"
    assert "exit code 3" in result.summary
    assert result.metadata["exit_code"] == 3
    assert any("boom" in log for log in result.logs)


@pytest.mark.anyio
async def test_cli_execution_adapter_times_out(tmp_path: Path) -> None:
    adapter = CliExecutionAdapter()
    request = ExecutionRequest(
        project=_project(tmp_path),
        task=_task(),
        command=f'"{sys.executable}" -c "import time; time.sleep(1)"',
        metadata={"timeout_seconds": 0.05},
    )

    result = await adapter.run(request)

    assert result.status == "timeout"
    assert "timed out" in result.summary
    assert result.metadata["timed_out"] is True
    assert result.metadata["timeout_seconds"] == 0.05


@pytest.mark.anyio
async def test_github_actions_adapter_dispatches_workflow(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    adapter = GitHubActionsExecutionAdapter()
    monkeypatch.setenv("GITHUB_TOKEN", "token-from-env")

    captured: dict[str, object] = {}

    def fake_dispatch(url: str, token: str, payload: dict[str, object]) -> int:
        captured["url"] = url
        captured["token"] = token
        captured["payload"] = payload
        return 204

    monkeypatch.setattr(adapter, "_dispatch_workflow", fake_dispatch)

    request = ExecutionRequest(
        project=_project(tmp_path),
        task=_task(),
        command="build.yml",
        metadata={"ref": "feature/x", "inputs": {"target": "test"}},
    )

    result = await adapter.run(request)

    assert result.status == "dispatched"
    assert "dispatched" in result.summary
    assert captured["token"] == "token-from-env"
    assert str(captured["url"]).endswith("/actions/workflows/build.yml/dispatches")
    assert captured["payload"] == {"ref": "feature/x", "inputs": {"target": "test"}}
    assert result.metadata["http_status"] == 204


@pytest.mark.anyio
async def test_github_actions_adapter_returns_failed_on_http_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    adapter = GitHubActionsExecutionAdapter()
    monkeypatch.setenv("GITHUB_TOKEN", "token-from-env")

    def fake_dispatch(_: str, __: str, ___: dict[str, object]) -> int:
        raise HTTPError(
            url="https://api.github.com/repos/example/orchai/actions/workflows/build.yml/dispatches",
            code=404,
            msg="Not Found",
            hdrs=None,
            fp=io.BytesIO(b'{"message":"Not Found"}'),
        )

    monkeypatch.setattr(adapter, "_dispatch_workflow", fake_dispatch)

    request = ExecutionRequest(
        project=_project(tmp_path),
        task=_task(),
        command="build.yml",
    )

    result = await adapter.run(request)

    assert result.status == "failed"
    assert "HTTP 404" in result.summary
    assert result.metadata["http_status"] == 404
    assert result.logs == ['{"message":"Not Found"}']


@pytest.mark.anyio
async def test_github_actions_adapter_fails_without_token(tmp_path: Path) -> None:
    adapter = GitHubActionsExecutionAdapter()
    request = ExecutionRequest(
        project=_project(tmp_path),
        task=_task(),
        command="build.yml",
    )

    result = await adapter.run(request)

    assert result.status == "failed"
    assert "missing GitHub token" in result.summary

