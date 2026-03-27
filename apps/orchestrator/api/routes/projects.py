from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

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
    service: OrchestratorService = Depends(get_orchestrator_service),
) -> ProjectDetailResponse:
    project = service.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return _to_project_detail(project)


def _to_project_summary(project: Project) -> ProjectSummaryResponse:
    return ProjectSummaryResponse(
        project_id=project.project_id,
        name=project.name,
        chat_platform=project.chat_platform,
        repo_url=project.repo_url,
        default_branch=project.default_branch,
    )


def _to_project_detail(project: Project) -> ProjectDetailResponse:
    return ProjectDetailResponse(
        project_id=project.project_id,
        name=project.name,
        description=project.description,
        chat_platform=project.chat_platform,
        repo_url=project.repo_url,
        default_branch=project.default_branch,
        workspace_path=project.workspace_path,
        channel_bindings={key: value.channel_id for key, value in project.channel_bindings.items()},
    )
