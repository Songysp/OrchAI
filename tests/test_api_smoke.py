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

    status_response = client.get(f"/api/tasks/{payload['task_id']}")
    assert status_response.status_code == 200
    status_payload = status_response.json()
    assert status_payload["task_id"] == payload["task_id"]
    assert status_payload["project_id"] == "sample-slack-project"
