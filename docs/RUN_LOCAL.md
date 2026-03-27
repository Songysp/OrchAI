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
- `GET /api/tasks`
- `POST /api/tasks`
- `POST /api/tasks/{task_id}/status/{status}`
- `GET /api/approvals`
- `POST /api/approvals`
- `GET /api/decisions`
- `POST /api/decisions`
- `GET /api/conversations`
