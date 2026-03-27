# Run Locally

## Local Python

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e .
uvicorn apps.orchestrator.main:app --reload
```

On Windows PowerShell:

```powershell
py -3.10 -m venv .venv
.venv\Scripts\Activate.ps1
pip install .
uvicorn apps.orchestrator.main:app --reload
```

If your `pip` is newer, `pip install -e .` also works.

## Docker Compose

```bash
docker compose -f infra/docker-compose.yml up --build
```

The API will be available at `http://localhost:8000`.

## Initial API endpoints

- `GET /health`
- `GET /api/projects`
- `GET /api/projects/{project_id}`
- `POST /api/tasks`
- `GET /api/tasks/{task_id}`

## Task flow

`POST /api/tasks` both creates the task and runs the MVP orchestration flow.

Request body:

```json
{
  "project_id": "sample-slack-project",
  "user_input": "Build the first representative AI workflow"
}
```

This request simulates a `user-control` channel message:

- task is created,
- representative workflow runs,
- mock chat deliveries are routed to `user-control`, `ai-council`, and `ai-ops`,
- the final summary is returned by the API.
