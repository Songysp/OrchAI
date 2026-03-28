from __future__ import annotations

import asyncio
import json
import os
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from packages.domain.models import ExecutionBackend
from packages.execution.base import ExecutionAdapter, ExecutionRequest, ExecutionResult


class GitHubActionsExecutionAdapter(ExecutionAdapter):
    backend_name = ExecutionBackend.GITHUB_ACTIONS

    async def run(self, request: ExecutionRequest) -> ExecutionResult:
        try:
            owner, repository = self._parse_repository(request.project.repo_url)
        except ValueError as exc:
            return ExecutionResult(
                backend=self.backend_name,
                status="failed",
                summary=f"GitHub Actions execution failed: {exc}",
                metadata={"repo_url": request.project.repo_url},
            )

        workflow_id = request.command.strip()
        if not workflow_id:
            return ExecutionResult(
                backend=self.backend_name,
                status="failed",
                summary="GitHub Actions execution failed: workflow identifier is empty.",
                metadata={"repo": f"{owner}/{repository}"},
            )

        token = self._resolve_token(request)
        if token is None:
            return ExecutionResult(
                backend=self.backend_name,
                status="failed",
                summary="GitHub Actions execution failed: missing GitHub token.",
                metadata={"repo": f"{owner}/{repository}", "workflow_id": workflow_id},
            )

        ref = request.metadata.get("ref")
        if not isinstance(ref, str) or not ref.strip():
            ref = request.project.default_branch

        inputs = request.metadata.get("inputs")
        if not isinstance(inputs, dict):
            inputs = {}

        dispatch_url = (
            f"https://api.github.com/repos/{owner}/{repository}/actions/workflows/{workflow_id}/dispatches"
        )
        payload = {"ref": ref, "inputs": inputs}

        try:
            response_status = await asyncio.to_thread(
                self._dispatch_workflow,
                dispatch_url,
                token,
                payload,
            )
        except HTTPError as exc:
            detail = self._decode_error_body(exc)
            return ExecutionResult(
                backend=self.backend_name,
                status="failed",
                summary=(
                    f"GitHub Actions dispatch failed with HTTP {exc.code} for workflow "
                    f"'{workflow_id}' on {owner}/{repository}."
                ),
                logs=[detail] if detail else [],
                metadata={
                    "repo": f"{owner}/{repository}",
                    "workflow_id": workflow_id,
                    "dispatch_url": dispatch_url,
                    "ref": ref,
                    "http_status": exc.code,
                },
            )
        except URLError as exc:
            return ExecutionResult(
                backend=self.backend_name,
                status="failed",
                summary=f"GitHub Actions dispatch failed due to network error: {exc.reason}",
                metadata={
                    "repo": f"{owner}/{repository}",
                    "workflow_id": workflow_id,
                    "dispatch_url": dispatch_url,
                    "ref": ref,
                },
            )

        return ExecutionResult(
            backend=self.backend_name,
            status="dispatched",
            summary=(
                f"GitHub Actions workflow '{workflow_id}' dispatched for {owner}/{repository} on ref '{ref}'."
            ),
            metadata={
                "repo": f"{owner}/{repository}",
                "workflow_id": workflow_id,
                "dispatch_url": dispatch_url,
                "ref": ref,
                "inputs": inputs,
                "http_status": response_status,
            },
        )

    def _resolve_token(self, request: ExecutionRequest) -> str | None:
        metadata_token = request.metadata.get("github_token")
        if isinstance(metadata_token, str) and metadata_token.strip():
            return metadata_token.strip()
        env_token = os.getenv("GITHUB_TOKEN")
        if isinstance(env_token, str) and env_token.strip():
            return env_token.strip()
        return None

    def _parse_repository(self, repo_url: str) -> tuple[str, str]:
        parsed = urlparse(repo_url)
        if parsed.netloc and parsed.netloc != "github.com":
            raise ValueError("repo_url must point to github.com")

        path = parsed.path or repo_url
        if path.endswith(".git"):
            path = path[:-4]
        segments = [segment for segment in path.strip("/").split("/") if segment]
        if len(segments) < 2:
            raise ValueError("repo_url must include owner and repository")
        return segments[0], segments[1]

    def _dispatch_workflow(self, dispatch_url: str, token: str, payload: dict[str, object]) -> int:
        request = Request(
            dispatch_url,
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {token}",
                "X-GitHub-Api-Version": "2022-11-28",
                "Content-Type": "application/json",
                "User-Agent": "orchai-execution-adapter",
            },
        )
        with urlopen(request, timeout=15) as response:
            return response.status

    def _decode_error_body(self, exc: HTTPError) -> str:
        try:
            if exc.fp is None:
                return ""
            body = exc.fp.read().decode("utf-8", errors="replace").strip()
        except Exception:
            return ""
        return body
