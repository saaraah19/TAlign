"""
ParsedResume model.

The output of the FIRST LLM call in the pipeline: raw resume text ->
structured skills/experience/education. Deliberately a separate table
from ResumeAnalysis (the second LLM call's output) for a concrete reason
beyond "separation of concerns" as an abstract principle:

    A resume only needs to be PARSED once. It needs to be ALIGNMENT-
    ANALYZED once per job application. A candidate with one resume and
    five applications should trigger one extraction call and five
    (job-specific) alignment calls — not five redundant extractions of
    the same document.

`ResumeAnalysisService` checks for an existing completed ParsedResume
for a given `resume_id` before triggering a new extraction call; only a
missing/failed one, or an explicit re-parse request, causes a new row
here. Never overwritten — same versioning discipline as everything else
in this codebase (Job/Application status, ResumeAnalysis itself).
"""

import uuid
from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.resume import Resume


class ParsedResumeStatus(StrEnum):
    COMPLETED = "completed"
    FAILED = "failed"


class ParsedResume(Base):
    __tablename__ = "parsed_resumes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    resume_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False
    )

    # --- Structured extraction output (mirrors ExtractedResumeSchema) ---
    extracted_skills: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    experience_entries: Mapped[list[dict]] = mapped_column(JSONB, nullable=False, default=list)
    total_years_experience: Mapped[float | None] = mapped_column(Float, nullable=True)
    education: Mapped[list[dict]] = mapped_column(JSONB, nullable=False, default=list)
    certifications: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)

    # --- Versioning / provenance ---
    llm_provider: Mapped[str] = mapped_column(String(50), nullable=False)
    llm_model: Mapped[str] = mapped_column(String(100), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(50), nullable=False)

    status: Mapped[str] = mapped_column(String(20), nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    resume: Mapped["Resume"] = relationship()

    def __repr__(self) -> str:  # pragma: no cover
        return f"<ParsedResume id={self.id} resume_id={self.resume_id} status={self.status}>"
