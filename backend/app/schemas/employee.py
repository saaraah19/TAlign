"""
Employee / OnboardingTask / WorkflowRun read schemas.

Recruiter-facing only (wired into the `_PIPELINE_READ_ROLES`-gated
GET /applications/{id}/hire-workflow endpoint) — there is no
candidate-facing schema here because there is no candidate-facing
Employee Portal in this MVP (see CLAUDE.md's locked scope).
"""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.workflow_engine.status import HireWorkflowStatus


class OnboardingTaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    completed: bool


class EmployeeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    first_name: str
    last_name: str
    email: str
    job_title: str
    hire_date: date


class WorkflowRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workflow_name: str
    status: str
    completed_steps: list[str]
    failed_step: str | None
    error: str | None
    created_at: datetime


class HireWorkflowStatusRead(BaseModel):
    workflow_run: WorkflowRunRead | None
    employee: EmployeeRead | None
    onboarding_tasks: list[OnboardingTaskRead]

    @classmethod
    def from_status(cls, status: HireWorkflowStatus) -> "HireWorkflowStatusRead":
        return cls(
            workflow_run=(
                WorkflowRunRead.model_validate(status.workflow_run)
                if status.workflow_run
                else None
            ),
            employee=(EmployeeRead.model_validate(status.employee) if status.employee else None),
            onboarding_tasks=[
                OnboardingTaskRead.model_validate(t) for t in status.onboarding_tasks
            ],
        )
