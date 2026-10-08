"""
Dashboard read schemas.

Reuses existing schemas wherever the shape already matches
(`ApplicationWithCandidate` for "awaiting review", `EmailRead` for
pending drafts, `WorkflowRunRead` from schemas/employee.py for recent
workflow activity) rather than redefining near-duplicates -- only
`DashboardBriefRead`, `LowApplicantJobRead`, and `RecentAnalysisRead`
are genuinely new shapes this slice needs.
"""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.application import ApplicationWithCandidate
from app.schemas.email import EmailRead
from app.schemas.employee import WorkflowRunRead


class RecommendedActionRead(BaseModel):
    label: str
    application_id: str | None


class DashboardBriefRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    brief_date: date
    summary: str
    recommended_actions: list[RecommendedActionRead]
    created_at: datetime


class LowApplicantJobRead(BaseModel):
    job_id: uuid.UUID
    title: str
    applicant_count: int


class RecentAnalysisRead(BaseModel):
    analysis_id: uuid.UUID
    application_id: uuid.UUID
    candidate_name: str
    job_title: str
    overall_score: float | None
    analyzed_at: datetime | None


class DashboardKPIsRead(BaseModel):
    """
    The Dashboard's top-line numbers. `active_candidates` deliberately
    excludes HIRED and REJECTED applications (see DashboardService.
    get_dashboard's comment) -- it answers "how many people are you
    actively considering right now," not "how many ever applied."
    `stage_counts` carries all six ApplicationStatus values, always,
    even at zero, so the funnel UI never has to guess whether a missing
    key means zero or not-yet-computed.
    """

    open_jobs: int
    active_candidates: int
    interviewing: int
    pending_actions: int
    stage_counts: dict[str, int]


class DashboardRead(BaseModel):
    brief: DashboardBriefRead | None
    kpis: DashboardKPIsRead
    awaiting_review: list[ApplicationWithCandidate]
    low_applicant_jobs: list[LowApplicantJobRead]
    recent_analyses: list[RecentAnalysisRead]
    recent_workflow_runs: list[WorkflowRunRead]
    pending_drafts: list[EmailRead]
