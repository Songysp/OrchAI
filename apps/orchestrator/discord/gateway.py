from __future__ import annotations

import asyncio
import logging
import os
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Protocol

from apps.orchestrator.discord.service import DiscordEventTranslator
from apps.orchestrator.services.chat_ingress_service import ChatIngressService
from apps.orchestrator.services.orchestrator_service import OrchestratorService
from packages.domain.models import Project

logger = logging.getLogger(__name__)

try:
    import discord as discord_sdk
except Exception:  # pragma: no cover - exercised via runtime fallback
    discord_sdk = None


class _GatewayClientProtocol(Protocol):
    def set_message_handler(self, handler: Callable[[dict[str, Any]], Awaitable[None]]) -> None: ...

    async def start(self, token: str) -> None: ...

    async def close(self) -> None: ...


@dataclass
class DiscordGatewayConfig:
    bot_token: str | None

    @classmethod
    def from_env(cls) -> "DiscordGatewayConfig":
        return cls(bot_token=os.getenv("DISCORD_BOT_TOKEN"))

    @property
    def enabled(self) -> bool:
        return bool(self.bot_token)


class _DiscordGatewayClient:
    def __init__(self) -> None:
        if discord_sdk is None:
            raise RuntimeError("discord.py is required for Discord gateway runtime")

        intents = discord_sdk.Intents.default()
        intents.guilds = True
        intents.messages = True
        intents.message_content = True

        self._client = discord_sdk.Client(intents=intents)
        self._message_handler: Callable[[dict[str, Any]], Awaitable[None]] | None = None

        @self._client.event
        async def on_message(message: Any) -> None:
            if self._message_handler is None:
                return
            await self._message_handler(
                {
                    "type": "message_create",
                    "id": str(getattr(message, "id", "")),
                    "channel_id": str(getattr(getattr(message, "channel", None), "id", "")),
                    "content": str(getattr(message, "content", "")),
                    "author": {
                        "id": str(getattr(getattr(message, "author", None), "id", "")),
                        "username": str(getattr(getattr(message, "author", None), "name", "")),
                        "bot": bool(getattr(getattr(message, "author", None), "bot", False)),
                    },
                }
            )

    def set_message_handler(self, handler: Callable[[dict[str, Any]], Awaitable[None]]) -> None:
        self._message_handler = handler

    async def start(self, token: str) -> None:
        await self._client.start(token)

    async def close(self) -> None:
        await self._client.close()


class DiscordGatewayRuntime:
    """Discord gateway runtime for receiving real bot events."""

    def __init__(
        self,
        orchestrator: OrchestratorService,
        ingress: ChatIngressService,
        *,
        config: DiscordGatewayConfig | None = None,
        translator: DiscordEventTranslator | None = None,
        client_factory: Any | None = None,
    ) -> None:
        self.orchestrator = orchestrator
        self.ingress = ingress
        self.config = config or DiscordGatewayConfig.from_env()
        self.translator = translator or DiscordEventTranslator()
        self.client_factory = client_factory or self._build_default_client
        self.uses_default_client_factory = client_factory is None
        self.client: _GatewayClientProtocol | None = None
        self.runner_task: asyncio.Task[None] | None = None
        self.started = False

    async def start(self) -> bool:
        if not self.config.enabled:
            logger.info("Discord gateway runtime disabled: missing DISCORD_BOT_TOKEN")
            return False
        if self.uses_default_client_factory and discord_sdk is None:
            logger.warning("Discord gateway runtime disabled: discord.py is not installed")
            return False

        client = self.client_factory(self.config)
        client.set_message_handler(self._process_message_payload)
        self.runner_task = asyncio.create_task(client.start(self.config.bot_token or ""))
        self.runner_task.add_done_callback(self._on_runner_done)
        self.client = client
        self.started = True
        logger.info("Discord gateway runtime started")
        return True

    async def stop(self) -> None:
        if self.client is None:
            return

        await self.client.close()
        if self.runner_task is not None:
            try:
                await asyncio.wait_for(self.runner_task, timeout=5)
            except asyncio.TimeoutError:
                self.runner_task.cancel()
            except asyncio.CancelledError:
                pass
            self.runner_task = None

        self.client = None
        self.started = False
        logger.info("Discord gateway runtime stopped")

    def _build_default_client(self, _: DiscordGatewayConfig) -> _GatewayClientProtocol:
        return _DiscordGatewayClient()

    def _on_runner_done(self, task: asyncio.Task[None]) -> None:
        if task.cancelled():
            return
        exc = task.exception()
        if exc is not None:
            logger.exception("Discord gateway runtime terminated with error", exc_info=exc)
        self.started = False

    async def _process_message_payload(self, payload: dict[str, Any]) -> None:
        channel_id = str(payload.get("channel_id") or "")
        if not channel_id:
            return

        project = self._resolve_project(channel_id)
        if project is None:
            logger.debug("Discord event ignored: no project bound to channel %s", channel_id)
            return

        try:
            translated = self.translator.translate(project, payload)
        except ValueError:
            logger.debug(
                "Discord event ignored: unbound channel %s for project %s",
                channel_id,
                project.project_id,
            )
            return
        if translated is None:
            return

        try:
            await self.ingress.handle_event(translated)
        except Exception:  # pragma: no cover - defensive runtime logging
            logger.exception("Failed to process Discord gateway event for project %s", project.project_id)

    def _resolve_project(self, channel_id: str) -> Project | None:
        for project in self.orchestrator.list_projects():
            if project.chat_platform.lower() != "discord":
                continue
            for binding in project.channel_bindings.values():
                if binding.channel_id == channel_id:
                    return project
        return None
