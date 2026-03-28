from fastapi.testclient import TestClient

from apps.orchestrator.api.deps import get_orchestrator_service
from apps.orchestrator.main import app
from packages.domain.models import ExecutionBackend
from packages.execution import ExecutionRequest, ExecutionResult


client = TestClient(app)


def test_healthcheck() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_projects_seeded_from_config() -> None:
    response = client.get("/api/projects")
    assert response.status_code == 200
    project_ids = {project["project_id"] for project in response.json()}
    assert "sample-slack-project" in project_ids
    assert "sample-discord-project" in project_ids


def test_project_detail_includes_runtime_status() -> None:
    response = client.get("/api/projects/sample-slack-project")
    assert response.status_code == 200
    payload = response.json()
    assert payload["project_id"] == "sample-slack-project"
    assert isinstance(payload["runtime_enabled"], bool)
    assert isinstance(payload["runtime_started"], bool)
    assert payload["runtime_mode"] in {"running", "stopped", "disabled", "unavailable"}


def test_create_task_runs_orchestration_and_returns_summary() -> None:
    response = client.post(
        "/api/tasks",
        json={
            "project_id": "sample-slack-project",
            "user_input": "Create the MVP representative orchestration flow",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["project_id"] == "sample-slack-project"
    assert payload["task_id"]
    assert payload["final_stage"] in {"completed", "waiting_human"}
    assert payload["decision_id"]
    assert payload["chat_delivery_count"] >= 1

    status_response = client.get(f"/api/tasks/{payload['task_id']}")
    assert status_response.status_code == 200
    status_payload = status_response.json()
    assert status_payload["task_id"] == payload["task_id"]
    assert status_payload["project_id"] == "sample-slack-project"


def test_tasks_endpoint_returns_paginated_items() -> None:
    create_response = client.post(
        "/api/tasks",
        json={
            "project_id": "sample-slack-project",
            "user_input": "List API pagination smoke check",
        },
    )
    assert create_response.status_code == 200

    response = client.get("/api/tasks", params={"project_id": "sample-slack-project", "limit": 5, "offset": 0})
    assert response.status_code == 200
    payload = response.json()
    assert payload["limit"] == 5
    assert payload["offset"] == 0
    assert payload["total"] >= 1
    assert len(payload["items"]) >= 1

    item = payload["items"][0]
    assert item["project_id"] == "sample-slack-project"
    assert "task_id" in item
    assert "status" in item
    assert "stage" in item
    assert "created_at" in item
    assert "updated_at" in item


def test_decisions_endpoint_returns_paginated_items() -> None:
    create_response = client.post(
        "/api/tasks",
        json={
            "project_id": "sample-slack-project",
            "user_input": "Decision list API smoke check",
        },
    )
    assert create_response.status_code == 200
    task_payload = create_response.json()

    response = client.get(
        "/api/decisions",
        params={
            "project_id": "sample-slack-project",
            "task_id": task_payload["task_id"],
            "limit": 5,
            "offset": 0,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["limit"] == 5
    assert payload["offset"] == 0
    assert payload["total"] >= 1
    assert len(payload["items"]) >= 1

    item = payload["items"][0]
    assert item["project_id"] == "sample-slack-project"
    assert item["task_id"] == task_payload["task_id"]
    assert "decision_id" in item
    assert "summary" in item
    assert "chosen_option" in item
    assert "created_at" in item


def test_approval_api_can_approve_and_resume_task() -> None:
    create_response = client.post(
        "/api/tasks",
        json={
            "project_id": "sample-slack-project",
            "user_input": "Review auth and schema changes for the orchestration layer",
        },
    )
    assert create_response.status_code == 200
    created = create_response.json()
    assert created["approval_required"] is True
    approval_id = created["approval_id"]
    assert approval_id

    approve_response = client.post(
        f"/api/approvals/{approval_id}/approve",
        json={
            "approved_by": "tester",
            "comment": "Approved for resume",
            "resume_task": True,
        },
    )
    assert approve_response.status_code == 200
    approval_payload = approve_response.json()
    assert approval_payload["approval"]["status"] == "approved"
    assert approval_payload["resumed"] is True
    assert approval_payload["task_stage"] == "completed"
    assert approval_payload["task_status"] == "completed"


def test_approvals_list_schema_review_contract() -> None:
    create_response = client.post(
        "/api/tasks",
        json={
            "project_id": "sample-slack-project",
            "user_input": "Review auth and schema changes for approval queue list",
        },
    )
    assert create_response.status_code == 200
    created = create_response.json()
    assert created["approval_required"] is True

    list_response = client.get("/api/approvals", params={"project_id": "sample-slack-project"})
    assert list_response.status_code == 200
    approvals = list_response.json()
    assert isinstance(approvals, list)
    assert len(approvals) >= 1

    item = approvals[0]
    assert "approval_id" in item
    assert "task_id" in item
    assert "project_id" in item
    assert "status" in item
    assert "approved_by" in item
    assert "comment" in item
    assert "created_at" in item


def test_conversations_endpoint_returns_history_items() -> None:
    create_response = client.post(
        "/api/tasks",
        json={
            "project_id": "sample-slack-project",
            "user_input": "Conversation history endpoint smoke check",
        },
    )
    assert create_response.status_code == 200
    task_payload = create_response.json()

    response = client.get(
        "/api/conversations",
        params={
            "project_id": "sample-slack-project",
            "task_id": task_payload["task_id"],
            "limit": 5,
            "offset": 0,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["limit"] == 5
    assert payload["offset"] == 0
    assert payload["total"] >= 1
    assert len(payload["items"]) >= 1

    item = payload["items"][0]
    assert item["project_id"] == "sample-slack-project"
    assert item["task_id"] == task_payload["task_id"]
    assert "conversation_id" in item
    assert "domain" in item
    assert "title" in item
    assert "messages" in item
    assert len(item["messages"]) >= 1

    message = item["messages"][0]
    assert "message_id" in message
    assert "domain" in message
    assert "role" in message
    assert "content" in message


def test_executions_and_artifacts_endpoints_return_logged_results() -> None:
    create_response = client.post(
        "/api/tasks",
        json={
            "project_id": "sample-slack-project",
            "user_input": "Execution log API smoke check",
        },
    )
    assert create_response.status_code == 200
    task_payload = create_response.json()

    service = get_orchestrator_service()
    task = service.task_service.get_task(task_payload["task_id"])
    project = service.get_project("sample-slack-project")
    assert task is not None
    assert project is not None

    execution_run = service.record_execution_result(
        request=ExecutionRequest(
            project=project,
            task=task,
            command="pytest -q",
            metadata={"trigger": "api-smoke"},
        ),
        result=ExecutionResult(
            backend=ExecutionBackend(project.execution_backend or ExecutionBackend.CLI.value),
            status="completed",
            summary="Execution finished in smoke test.",
            logs=["stdout smoke line", "stderr smoke line"],
            metadata={"exit_code": 0},
        ),
    )

    executions_response = client.get(
        "/api/executions",
        params={
            "project_id": "sample-slack-project",
            "task_id": task_payload["task_id"],
            "limit": 10,
            "offset": 0,
        },
    )
    assert executions_response.status_code == 200
    executions_payload = executions_response.json()
    assert executions_payload["total"] >= 1
    execution_item = executions_payload["items"][0]
    assert execution_item["execution_id"] == execution_run.execution_id
    assert execution_item["status"] == "completed"
    assert execution_item["backend"] in {"cli", "github_actions"}
    assert len(execution_item["artifact_ids"]) >= 1

    artifacts_response = client.get(
        f"/api/executions/{execution_run.execution_id}/artifacts",
        params={
            "project_id": "sample-slack-project",
            "limit": 10,
            "offset": 0,
        },
    )
    assert artifacts_response.status_code == 200
    artifacts_payload = artifacts_response.json()
    assert artifacts_payload["total"] >= 1
    artifact_item = artifacts_payload["items"][0]
    assert artifact_item["execution_id"] == execution_run.execution_id
    assert artifact_item["project_id"] == "sample-slack-project"
    assert artifact_item["relative_path"].startswith("execution_artifacts/files/")
