from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from apps.orchestrator.api.deps import get_chat_ingress_service, get_orchestrator_service
from apps.orchestrator.api.routes.approvals import router as approvals_router
from apps.orchestrator.api.routes.decisions import router as decisions_router
from apps.orchestrator.api.routes.health import router as health_router
from apps.orchestrator.api.routes.projects import router as projects_router
from apps.orchestrator.api.routes.tasks import router as tasks_router
from apps.orchestrator.discord.gateway import DiscordGatewayRuntime
from apps.orchestrator.discord.routes import router as discord_router
from apps.orchestrator.slack.socket_mode import SlackSocketModeRuntime
from apps.orchestrator.slack.routes import router as slack_router


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting AI Dev Team Platform orchestrator API")
    discord_gateway_runtime = DiscordGatewayRuntime(
        orchestrator=get_orchestrator_service(),
        ingress=get_chat_ingress_service(),
    )
    slack_socket_runtime = SlackSocketModeRuntime(
        orchestrator=get_orchestrator_service(),
        ingress=get_chat_ingress_service(),
    )
    app.state.discord_gateway_runtime = discord_gateway_runtime
    app.state.slack_socket_runtime = slack_socket_runtime
    await discord_gateway_runtime.start()
    await slack_socket_runtime.start()
    yield
    await discord_gateway_runtime.stop()
    await slack_socket_runtime.stop()
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
    app.include_router(decisions_router, prefix="/api")
    app.include_router(approvals_router, prefix="/api")
    app.include_router(slack_router, prefix="/api")
    app.include_router(discord_router, prefix="/api")
    return app


app = create_app()
