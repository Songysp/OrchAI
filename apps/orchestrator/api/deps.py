from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from packages.domain.services.orchestrator import OrchestratorService
from packages.domain.services.registry import PlatformRegistry


@lru_cache(maxsize=1)
def get_registry() -> PlatformRegistry:
    root_path = Path(__file__).resolve().parents[3]
    return PlatformRegistry(root_path=root_path)


def get_orchestrator_service() -> OrchestratorService:
    return OrchestratorService(registry=get_registry())
