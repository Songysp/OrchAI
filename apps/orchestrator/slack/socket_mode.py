from __future__ import annotations

import asyncio
import logging
import os
from dataclasses import dataclass
from typing import Any, Protocol

from apps.orchestrator.services.chat_ingress_service import ChatIngressService
from apps.orchestrator.services.orchestrator_service import OrchestratorService
from apps.orchestrator.slack.service import SlackEventTranslator
from packages.domain.models import Project

logger = logging.getLogger(__name__)

try:
    from slack_sdk.socket_mode.aiohttp import SocketModeClient as SlackSdkSocketModeClient
    from slack_sdk.socket_mode.request import SocketModeRequest
    from slack_sdk.socket_mode.response import SocketModeResponse
    from slack_sdk.web.async_client import AsyncWebClient
except Exception:  # pragma: no cover - exercised through runtime fallback path
    SlackSdkSocketModeClient = None
    SocketModeRequest = Any  # type: ignore[assignment]
    SocketModeResponse = None
    AsyncWebClient = None


class _SocketClientProtocol(Protocol):
    socket_mode_request_listeners: list[Any]

    async def connect(self) -> None: ...

    async def disconnect(self) -> None: ...

    async def send_socket_mode_response(self, response: Any) -> None: ...


@dataclass
class SlackSocketModeConfig:
    app_token: str | None
    bot_token: str | None

    @classmethod
    def from_env(cls) -> "SlackSocketModeConfig":
        return cls(
            app_token=os.getenv("SLACK_APP_TOKEN"),
            bot_token=os.getenv("SLACK_BOT_TOKEN"),
        )

    @property
    def enabled(self) -> bool:
        return bool(self.app_token)


class SlackSocketModeRuntime:
    """Socket Mode runtime for receiving real Slack events."""

    def __init__(
        self,
        orchestrator: OrchestratorService,
        ingress: ChatIngressService,
        *,
        config: SlackSocketModeConfig | None = None,
        translator: SlackEventTranslator | None = None,
        client_factory: Any | None = None,
    ) -> None:
        self.orchestrator = orchestrator
        self.ingress = ingress
        self.config = config or SlackSocketModeConfig.from_env()
        self.translator = translator or SlackEventTranslator()
        self.client_factory = client_factory or self._build_default_client
        self.client: _SocketClientProtocol | None = None
        self.started = False

    async def start(self) -> bool:
        if not self.config.enabled:
            logger.info("Slack Socket Mode disabled: missing SLACK_APP_TOKEN")
            return False
        if SlackSdkSocketModeClient is None or SocketModeResponse is None:
            logger.warning("Slack Socket Mode disabled: slack_sdk is not installed")
            return False

        client = self.client_factory(self.config)
        client.socket_mode_request_listeners.append(self._on_socket_request)
        await client.connect()
        self.client = client
        self.started = True
        logger.info("Slack Socket Mode connected")
        return True

    async def stop(self) -> None:
        if self.client is None:
            return
        await self.client.disconnect()
        self.client = None
        self.started = False
        logger.info("Slack Socket Mode disconnected")

    def _build_default_client(self, config: SlackSocketModeConfig) -> _SocketClientProtocol:
        if SlackSdkSocketModeClient is None:
            raise RuntimeError("slack_sdk is required for Socket Mode")
        kwargs: dict[str, Any] = {"app_token": config.app_token}
        if config.bot_token and AsyncWebClient is not None:
            kwargs["web_client"] = AsyncWebClient(token=config.bot_token)
        return SlackSdkSocketModeClient(**kwargs)

    async def _on_socket_request(self, client: _SocketClientProtocol, request: SocketModeRequest) -> None:
        if getattr(request, "envelope_id", None) and SocketModeResponse is not None:
            response = SocketModeResponse(envelope_id=request.envelope_id)
            await client.send_socket_mode_response(response)

        payload = getattr(request, "payload", None)
        if not isinstance(payload, dict):
            return
        if payload.get("type") != "event_callback":
            return

        asyncio.create_task(self._process_event_payload(payload))

    async def _process_event_payload(self, payload: dict[str, Any]) -> None:
        event = payload.get("event")
        if not isinstance(event, dict):
            return

        channel_id = str(event.get("channel") or "")
        if not channel_id:
            return

        project = self._resolve_project(channel_id)
        if project is None:
            logger.debug("Slack event ignored: no project bound to channel %s", channel_id)
            return

        translated = self.translator.translate(project, payload)
        if translated is None:
            return

        try:
            await self.ingress.handle_event(translated)
        except Exception:  # pragma: no cover - defensive runtime logging
            logger.exception("Failed to process Slack Socket Mode event for project %s", project.project_id)

    def _resolve_project(self, channel_id: str) -> Project | None:
        for project in self.orchestrator.list_projects():
            if project.chat_platform.lower() != "slack":
                continue
            for binding in project.channel_bindings.values():
                if binding.channel_id == channel_id:
                    return project
        return None
