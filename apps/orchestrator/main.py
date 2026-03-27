from __future__ import annotations

from fastapi import FastAPI

from apps.orchestrator.api.routes.approvals import router as approvals_router
from apps.orchestrator.api.routes.conversations import router as conversations_router
from apps.orchestrator.api.routes.decisions import router as decisions_router
from apps.orchestrator.api.routes.health import router as health_router
from apps.orchestrator.api.routes.projects import router as projects_router
from apps.orchestrator.api.routes.tasks import router as tasks_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="AI Dev Team Platform Orchestrator",
        version="0.1.0",
        description="Reusable AI dev team orchestration API for chat adapters and future dashboards.",
    )
    app.include_router(health_router)
    app.include_router(projects_router, prefix="/api")
    app.include_router(tasks_router, prefix="/api")
    app.include_router(approvals_router, prefix="/api")
    app.include_router(decisions_router, prefix="/api")
    app.include_router(conversations_router, prefix="/api")
    return app


app = create_app()
