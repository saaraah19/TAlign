"""
ResumeAnalysis schemas.

`AnalysisProgressStatusRead` is intentionally the ONLY schema exposed to
candidates — it carries a status string and nothing else. Every other
schema here (`ResumeAnalysisRead`, `SkillMatchRead`, etc.) carries
score/skill/strength/concern content and is wired ONLY into
recruiter-facing endpoints (see app/api/v1/applications.py's RBAC —
`_PIPELINE_READ_ROLES`). This split is enforced by which schema a route
declares as its `response_model`, not by field-level filtering after the
fact — a candidate-facing route literally has no code path that could
serialize analysis content, because it never imports these types.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.resume_analysis import AnalysisProgressStatus


class AttachResumeRequest(BaseModel):
    resume_id: uuid.UUID


class AnalysisProgressStatusRead(BaseModel):
    """
    Safe for ANY role, including candidates — carries only a coarse
    status enum, never score/skills/strengths/concerns. See module
    docstring.
    """

    status: AnalysisProgressStatus


class SkillMatchRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    skill: str
    match_state: str
    evidence: str | None


class ExperienceFitRead(BaseModel):
    candidate_relevant_years: float | None = None
    meets_minimum: bool | None = None
    justification: str | None = None


class ResumeAnalysisRead(BaseModel):
    """
    Recruiter-facing only — never wired into a candidate-accessible
    route. See module docstring.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    application_id: uuid.UUID
    parsed_resume_id: uuid.UUID
    status: str

    overall_score: float | None
    required_skills_score_pct: float | None
    preferred_skills_score_pct: float | None
    experience_score_pct: float | None
    scoring_algorithm_version: str | None

    required_skills_result: list[SkillMatchRead]
    preferred_skills_result: list[SkillMatchRead]
    experience_fit: ExperienceFitRead | None
    matched_skills: list[str]
    missing_skills: list[str]
    strengths: list[str]
    potential_concerns: list[str]
    explanation: str | None

    llm_provider: str | None
    llm_model: str | None
    prompt_version: str | None
    error_message: str | None

    analyzed_at: datetime | None
    created_at: datetime


class ResumeAnalysisHistoryResponse(BaseModel):
    items: list[ResumeAnalysisRead]
