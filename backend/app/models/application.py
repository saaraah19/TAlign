"""
Application model.

The central relationship between Candidate and Job. Per instruction:
Candidate (a User with account_type=CANDIDATE — see Slice 1) must NEVER
carry application-specific state. Pipeline status, and later alignment
score, summary, and AI analysis, all live here, on Application, never on
User or Job. A single candidate can hold many Applications across many
companies, each independently.

`company_id` is denormalized from `job.company_id` at creation time and
never changes afterward — see ApplicationService.apply(). This exists
purely for query convenience (company-scoped recruiter queries filter
directly on Application without a join through Job) and is not a second
source of truth: it's set once, from the Job, and the Job's company can
never change after creation either.

Candidate validity (candidate_id must reference a User with
account_type='candidate') is NOT expressed as a DB constraint — unlike
Slice 1's ck_users_company_assignment, this check spans two tables
(applications.candidate_id -> users.account_type), which plain CHECK
constraints can't express without a trigger. A trigger was considered
and rejected as unnecessary complexity for the MVP: ApplicationService
is the only code path that ever inserts an Application (the repository
has no rule-checking of its own, same convention as every other
repository), so the service-layer assertion
(`ApplicationService._assert_valid_candidate`) is the sole enforcement
point, and it's the sole *insert* point too.
"""

import uuid
from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.company import Company
    from app.models.job import Job
    from app.models.resume import Resume
    from app.models.user import User


class ApplicationStatus(StrEnum):
    APPLIED = "applied"
    SCREENING = "screening"
    INTERVIEW = "interview"
    OFFER = "offer"
    HIRED = "hired"
    REJECTED = "rejected"


class Application(Base):
    __tablename__ = "applications"
    __table_args__ = (
        UniqueConstraint("candidate_id", "job_id", name="uq_applications_candidate_job"),
        CheckConstraint(
            "status IN ('applied', 'screening', 'interview', 'offer', 'hired', 'rejected')",
            name="ck_applications_status_valid",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False
    )
    #: Denormalized from job.company_id at creation — see module docstring.
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )

    #: Currently-selected resume for this application. NULLABLE — an
    #: application can exist before any resume is attached (candidate
    #: applies, then attaches a resume separately). Kept as its own
    #: column rather than derived from the latest ResumeAnalysis because
    #: those two things can legitimately differ: a candidate can swap
    #: their attached resume without an analysis having run yet, and the
    #: "current resume" must still be knowable in that gap. See
    #: docs/04_slice4_resume_intelligence.md section 11 for the full
    #: reasoning on why this wasn't redundant with
    #: ResumeAnalysis.parsed_resume_id -> ParsedResume.resume_id.
    resume_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resumes.id", ondelete="SET NULL"), nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=ApplicationStatus.APPLIED
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    candidate: Mapped["User"] = relationship(foreign_keys=[candidate_id])
    job: Mapped["Job"] = relationship()
    company: Mapped["Company"] = relationship()
    resume: Mapped["Resume | None"] = relationship()

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Application id={self.id} job_id={self.job_id} status={self.status}>"
