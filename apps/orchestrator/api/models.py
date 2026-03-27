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
    chat_delivery_count: int = 0


class TaskStatusResponse(BaseModel):
    task_id: str
    project_id: str
    status: str
    stage: str
    updated_at: datetime
    summary: str | None = None


class TaskListItemResponse(BaseModel):
    task_id: str
    project_id: str
    title: str
    status: str
    stage: str
    created_at: datetime
    updated_at: datetime
    summary: str | None = None


class TaskListResponse(BaseModel):
    items: list[TaskListItemResponse]
    total: int
    limit: int
    offset: int


class DecisionResponse(BaseModel):
    decision_id: str
    task_id: str
    project_id: str
    summary: str
    chosen_option: str
    created_at: datetime


class DecisionListResponse(BaseModel):
    items: list[DecisionResponse]
    total: int
    limit: int
    offset: int


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
    runtime_enabled: bool
    runtime_started: bool
    runtime_mode: str


class ApprovalActionRequest(BaseModel):
    approved_by: str
    comment: str | None = None
    resume_task: bool = True


class ApprovalResponse(BaseModel):
    approval_id: str
    task_id: str
    project_id: str
    status: str
    approved_by: str | None = None
    comment: str | None = None
    created_at: datetime


class ApprovalActionResponse(BaseModel):
    approval: ApprovalResponse
    resumed: bool = False
    task_id: str
    task_stage: str
    task_status: str
