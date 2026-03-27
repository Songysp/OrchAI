from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from apps.orchestrator.api.deps import get_orchestrator_service
from apps.orchestrator.api.models import ProjectDetailResponse, ProjectSummaryResponse
from apps.orchestrator.services.orchestrator_service import OrchestratorService
from packages.domain.models import Project

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=list[ProjectSummaryResponse])
def list_projects(service: OrchestratorService = Depends(get_orchestrator_service)) -> list[ProjectSummaryResponse]:
    return [_to_project_summary(project) for project in service.list_projects()]


@router.get("/{project_id}", response_model=ProjectDetailResponse)
def get_project(
    project_id: str,
    request: Request,
    service: OrchestratorService = Depends(get_orchestrator_service),
) -> ProjectDetailResponse:
    project = service.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return _to_project_detail(project, request)


def _to_project_summary(project: Project) -> ProjectSummaryResponse:
    return ProjectSummaryResponse(
        project_id=project.project_id,
        name=project.name,
        chat_platform=project.chat_platform,
        repo_url=project.repo_url,
        default_branch=project.default_branch,
    )


def _to_project_detail(project: Project, request: Request) -> ProjectDetailResponse:
    runtime_enabled, runtime_started, runtime_mode = _resolve_runtime_status(project, request)
    return ProjectDetailResponse(
        project_id=project.project_id,
        name=project.name,
        description=project.description,
        chat_platform=project.chat_platform,
        repo_url=project.repo_url,
        default_branch=project.default_branch,
        workspace_path=project.workspace_path,
        channel_bindings={key: value.channel_id for key, value in project.channel_bindings.items()},
        runtime_enabled=runtime_enabled,
        runtime_started=runtime_started,
        runtime_mode=runtime_mode,
    )


def _resolve_runtime_status(project: Project, request: Request) -> tuple[bool, bool, str]:
    platform = project.chat_platform.lower()
    runtime = None
    if platform == "slack":
        runtime = getattr(request.app.state, "slack_socket_runtime", None)
    elif platform == "discord":
        runtime = getattr(request.app.state, "discord_gateway_runtime", None)

    if runtime is None:
        return False, False, "unavailable"

    config = getattr(runtime, "config", None)
    enabled = bool(getattr(config, "enabled", False))
    started = bool(getattr(runtime, "started", False))

    if not enabled:
        mode = "disabled"
    elif started:
        mode = "running"
    else:
        mode = "stopped"

    return enabled, started, mode
