from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path

from apps.orchestrator.services.chat_ingress_service import ChatIngressService
from apps.orchestrator.services.orchestrator_service import OrchestratorService
from packages.domain.services.registry import PlatformRegistry

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_registry() -> PlatformRegistry:
    root_path = Path(__file__).resolve().parents[3]
    logger.info("Initializing platform registry from root path %s", root_path)
    return PlatformRegistry(root_path=root_path)


def get_orchestrator_service() -> OrchestratorService:
    return OrchestratorService(registry=get_registry())


def get_chat_ingress_service() -> ChatIngressService:
    return ChatIngressService(orchestrator=get_orchestrator_service())
