"""Application schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.application import ApplicationStatus


class ApplicationCreateRequest(BaseModel):
    job_id: uuid.UUID


class ApplicationStatusTransitionRequest(BaseModel):
    target_status: ApplicationStatus


class ApplicationJobSummary(BaseModel):
    """Minimal job info embedded in a candidate's application view."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    company_id: uuid.UUID


class ApplicationCandidateSummary(BaseModel):
    """Minimal candidate info embedded in a recruiter's pipeline view."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    first_name: str
    last_name: str
    email: str


class ApplicationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    candidate_id: uuid.UUID
    job_id: uuid.UUID
    company_id: uuid.UUID
    status: ApplicationStatus
    created_at: datetime
    updated_at: datetime


class ApplicationWithJob(ApplicationRead):
    """Candidate-facing: includes the job being applied to."""

    job: ApplicationJobSummary


class ApplicationWithCandidate(ApplicationRead):
    """Recruiter-facing: includes the applying candidate's basic info."""

    candidate: ApplicationCandidateSummary
    job: ApplicationJobSummary


class ApplicationListResponse(BaseModel):
    items: list[ApplicationWithJob]
    total: int
    page: int
    page_size: int


class PipelineListResponse(BaseModel):
    items: list[ApplicationWithCandidate]
    total: int
    page: int
    page_size: int
