from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class CreateTaskRequest(BaseModel):
    project_id: str
    user_input: str


class TaskRunResponse(BaseModel):
    task_id: str
    project_id: str
    title: str
    final_status: str
    final_stage: str
    summary: str
    decision_id: str
    approval_required: bool
    approval_id: str | None = None


class TaskStatusResponse(BaseModel):
    task_id: str
    project_id: str
    status: str
    stage: str
    updated_at: datetime
    summary: str | None = None


class ProjectSummaryResponse(BaseModel):
    project_id: str
    name: str | None = None
    chat_platform: str
    repo_url: str
    default_branch: str


class ProjectDetailResponse(ProjectSummaryResponse):
    description: str | None = None
    workspace_path: str
    channel_bindings: dict[str, str]
