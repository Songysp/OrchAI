from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from apps.orchestrator.api.routes.health import router as health_router
from apps.orchestrator.api.routes.projects import router as projects_router
from apps.orchestrator.api.routes.tasks import router as tasks_router


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting AI Dev Team Platform orchestrator API")
    yield
    logger.info("Stopping AI Dev Team Platform orchestrator API")


def create_app() -> FastAPI:
    app = FastAPI(
        title="AI Dev Team Platform Orchestrator",
        version="0.1.0",
        description="Reusable AI dev team orchestration API for chat adapters and future dashboards.",
        lifespan=lifespan,
    )
    app.include_router(health_router)
    app.include_router(projects_router, prefix="/api")
    app.include_router(tasks_router, prefix="/api")
    return app


app = create_app()
