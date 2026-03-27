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
