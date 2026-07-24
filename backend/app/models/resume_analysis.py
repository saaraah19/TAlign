"""
ResumeAnalysis model.

The output of the SECOND LLM call: ParsedResume + Job.required_skills/
preferred_skills/min_years_experience -> alignment reasoning -> (our own
deterministic code, NOT the LLM) -> overall_score. One row per analysis
ATTEMPT for a given Application — re-analysis always inserts a new row;
nothing here is ever updated after `status` leaves `pending`. See
app/agents/resume_intelligence/scoring.py for exactly how
`overall_score` is computed from the stored match results below.

MatchState is three-valued, not boolean, per explicit product decision:
a skill genuinely not mentioned in a resume is NOT the same claim as "the
candidate doesn't have this skill" — the resume just may not have said
so. INSUFFICIENT_EVIDENCE exists specifically so the agent (and the
score) never silently treats "not mentioned" as "absent."
"""

import uuid
from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.application import Application
    from app.models.parsed_resume import ParsedResume


class MatchState(StrEnum):
    MATCHED = "matched"
    NOT_MATCHED = "not_matched"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class AnalysisStatus(StrEnum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class AnalysisProgressStatus(StrEnum):
    """
    NOT persisted — a derived, composite status computed by
    ResumeAnalysisService.get_progress_status() from Resume/ParsedResume/
    ResumeAnalysis together, for frontend polling (the "Uploading /
    Parsing / Analyzing / Complete / Failed" states). See that method
    for exactly how each value is derived.
    """

    NOT_STARTED = "not_started"
    PARSING = "parsing"
    ANALYZING = "analyzing"
    COMPLETE = "complete"
    FAILED = "failed"


class ResumeAnalysis(Base):
    __tablename__ = "resume_analyses"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'completed', 'failed')",
            name="ck_resume_analyses_status_valid",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False
    )
    parsed_resume_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("parsed_resumes.id", ondelete="CASCADE"), nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=AnalysisStatus.PENDING
    )

    # --- Score (computed by OUR code — see scoring.py — never by the LLM directly) ---
    overall_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    required_skills_score_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    preferred_skills_score_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    experience_score_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    scoring_algorithm_version: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # --- Structured reasoning output (mirrors AlignmentReasoningSchema) ---
    required_skills_result: Mapped[list[dict]] = mapped_column(
        JSONB, nullable=False, default=list
    )
    preferred_skills_result: Mapped[list[dict]] = mapped_column(
        JSONB, nullable=False, default=list
    )
    experience_fit: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    matched_skills: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    missing_skills: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    strengths: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    potential_concerns: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)

    # --- Versioning / provenance ---
    llm_provider: Mapped[str | None] = mapped_column(String(50), nullable=True)
    llm_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    prompt_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    analyzed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    application: Mapped["Application"] = relationship()
    parsed_resume: Mapped["ParsedResume"] = relationship()

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<ResumeAnalysis id={self.id} application_id={self.application_id} "
            f"status={self.status} score={self.overall_score}>"
        )
