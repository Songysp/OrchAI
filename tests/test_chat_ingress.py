import hashlib
import hmac
import json
import time

from fastapi.testclient import TestClient

from apps.orchestrator.main import create_app

SLACK_SIGNING_SECRET = "test-slack-signing-secret"


def _post_signed_slack_event(
    client: TestClient,
    project_id: str,
    payload: dict[str, object],
    *,
    signing_secret: str = SLACK_SIGNING_SECRET,
) -> object:
    body = json.dumps(payload, separators=(",", ":"))
    timestamp = str(int(time.time()))
    base = f"v0:{timestamp}:{body}".encode("utf-8")
    signature = "v0=" + hmac.new(
        signing_secret.encode("utf-8"),
        base,
        hashlib.sha256,
    ).hexdigest()
    return client.post(
        f"/api/integrations/slack/{project_id}/events",
        data=body.encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "X-Slack-Request-Timestamp": timestamp,
            "X-Slack-Signature": signature,
        },
    )


def test_slack_user_control_event_creates_and_runs_task() -> None:
    import os

    os.environ["SLACK_SIGNING_SECRET"] = SLACK_SIGNING_SECRET
    client = TestClient(create_app())

    response = _post_signed_slack_event(
        client,
        "sample-slack-project",
        {
            "type": "event_callback",
            "event": {
                "type": "message",
                "channel": "C_USER_CONTROL",
                "user": "U123",
                "text": "Implement auth-safe schema review workflow",
                "ts": "1710000000.000100",
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["accepted"] is True
    assert payload["action"] == "task_created"
    assert payload["task_id"]
    assert payload["status"] in {"blocked", "completed"}


def test_discord_user_control_event_creates_and_runs_task() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/integrations/discord/sample-discord-project/events",
        json={
            "type": "message_create",
            "id": "m-001",
            "channel_id": "discord-user-control",
            "content": "Plan the next builder workflow",
            "author": {"id": "user-1", "username": "song", "bot": False},
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["accepted"] is True
    assert payload["action"] == "task_created"
    assert payload["task_id"]


def test_slack_non_user_control_channel_is_ignored() -> None:
    import os

    os.environ["SLACK_SIGNING_SECRET"] = SLACK_SIGNING_SECRET
    client = TestClient(create_app())

    response = _post_signed_slack_event(
        client,
        "sample-slack-project",
        {
            "type": "event_callback",
            "event": {
                "type": "message",
                "channel": "C_AI_OPS",
                "user": "U123",
                "text": "ops chatter should not create a task",
                "ts": "1710000000.000200",
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["accepted"] is True
    assert payload["action"] == "ignored"
    assert payload["task_id"] is None


def test_slack_approve_command_resumes_waiting_task() -> None:
    import os

    os.environ["SLACK_SIGNING_SECRET"] = SLACK_SIGNING_SECRET
    client = TestClient(create_app())

    created = _post_signed_slack_event(
        client,
        "sample-slack-project",
        {
            "type": "event_callback",
            "event": {
                "type": "message",
                "channel": "C_USER_CONTROL",
                "user": "U123",
                "text": "Implement auth-safe schema review workflow",
                "ts": "1710000000.000300",
            },
        },
    )
    assert created.status_code == 200
    created_task_id = created.json()["task_id"]

    approvals = client.get("/api/approvals", params={"project_id": "sample-slack-project"})
    assert approvals.status_code == 200
    approval_id = next(
        item["approval_id"]
        for item in approvals.json()
        if item["task_id"] == created_task_id and item["status"] == "pending"
    )

    approved = _post_signed_slack_event(
        client,
        "sample-slack-project",
        {
            "type": "event_callback",
            "event": {
                "type": "message",
                "channel": "C_USER_CONTROL",
                "user": "U123",
                "text": f"/approve {approval_id} looks good",
                "ts": "1710000000.000301",
            },
        },
    )

    assert approved.status_code == 200
    payload = approved.json()
    assert payload["accepted"] is True
    assert payload["action"] == "approval_approved"
    assert payload["approval_id"] == approval_id
    assert payload["resumed"] is True
    assert payload["status"] == "completed"


def test_discord_reject_command_fails_waiting_task() -> None:
    client = TestClient(create_app())

    created = client.post(
        "/api/integrations/discord/sample-discord-project/events",
        json={
            "type": "message_create",
            "id": "m-002",
            "channel_id": "discord-user-control",
            "content": "Implement auth-safe schema review workflow",
            "author": {"id": "user-2", "username": "reviewer", "bot": False},
        },
    )
    assert created.status_code == 200
    created_task_id = created.json()["task_id"]

    approvals = client.get("/api/approvals", params={"project_id": "sample-discord-project"})
    assert approvals.status_code == 200
    approval_id = next(
        item["approval_id"]
        for item in approvals.json()
        if item["task_id"] == created_task_id and item["status"] == "pending"
    )

    rejected = client.post(
        "/api/integrations/discord/sample-discord-project/events",
        json={
            "type": "message_create",
            "id": "m-003",
            "channel_id": "discord-user-control",
            "content": f"/reject {approval_id} not safe enough",
            "author": {"id": "user-2", "username": "reviewer", "bot": False},
        },
    )

    assert rejected.status_code == 200
    payload = rejected.json()
    assert payload["accepted"] is True
    assert payload["action"] == "approval_rejected"
    assert payload["approval_id"] == approval_id
    assert payload["resumed"] is False
    assert payload["status"] == "failed"


def test_slack_help_command_returns_supported_commands() -> None:
    import os

    os.environ["SLACK_SIGNING_SECRET"] = SLACK_SIGNING_SECRET
    client = TestClient(create_app())

    response = _post_signed_slack_event(
        client,
        "sample-slack-project",
        {
            "type": "event_callback",
            "event": {
                "type": "message",
                "channel": "C_USER_CONTROL",
                "user": "U123",
                "text": "/help",
                "ts": "1710000000.000400",
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["accepted"] is True
    assert payload["action"] == "help"
    assert "/approvals" in payload["message"]


def test_discord_status_command_returns_task_status() -> None:
    client = TestClient(create_app())

    created = client.post(
        "/api/integrations/discord/sample-discord-project/events",
        json={
            "type": "message_create",
            "id": "m-004",
            "channel_id": "discord-user-control",
            "content": "Plan the next builder workflow",
            "author": {"id": "user-3", "username": "operator", "bot": False},
        },
    )
    assert created.status_code == 200
    task_id = created.json()["task_id"]

    response = client.post(
        "/api/integrations/discord/sample-discord-project/events",
        json={
            "type": "message_create",
            "id": "m-005",
            "channel_id": "discord-user-control",
            "content": f"/status {task_id}",
            "author": {"id": "user-3", "username": "operator", "bot": False},
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["accepted"] is True
    assert payload["action"] == "task_status"
    assert payload["task_id"] == task_id
    assert payload["status"] in {"completed", "blocked", "failed", "pending", "planning", "in_progress", "review", "testing"}


def test_slack_approvals_command_lists_pending_items() -> None:
    import os

    os.environ["SLACK_SIGNING_SECRET"] = SLACK_SIGNING_SECRET
    client = TestClient(create_app())

    created = _post_signed_slack_event(
        client,
        "sample-slack-project",
        {
            "type": "event_callback",
            "event": {
                "type": "message",
                "channel": "C_USER_CONTROL",
                "user": "U123",
                "text": "Implement auth-safe schema review workflow",
                "ts": "1710000000.000500",
            },
        },
    )
    assert created.status_code == 200

    response = _post_signed_slack_event(
        client,
        "sample-slack-project",
        {
            "type": "event_callback",
            "event": {
                "type": "message",
                "channel": "C_USER_CONTROL",
                "user": "U123",
                "text": "/approvals",
                "ts": "1710000000.000501",
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["accepted"] is True
    assert payload["action"] == "approvals_listed"
    assert "Pending approvals:" in payload["message"]


def test_slack_event_rejects_invalid_signature() -> None:
    import os

    os.environ["SLACK_SIGNING_SECRET"] = SLACK_SIGNING_SECRET
    client = TestClient(create_app())

    response = _post_signed_slack_event(
        client,
        "sample-slack-project",
        {
            "type": "event_callback",
            "event": {
                "type": "message",
                "channel": "C_USER_CONTROL",
                "user": "U123",
                "text": "invalid signature should be rejected",
                "ts": "1710000000.000600",
            },
        },
        signing_secret="wrong-secret",
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid Slack signature"
