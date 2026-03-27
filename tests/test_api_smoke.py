from fastapi.testclient import TestClient

from apps.orchestrator.main import app


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
