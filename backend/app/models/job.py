"""
Job model.

`JobStatus` and `EmploymentType` are defined here, not in `app/core/`,
deliberately: unlike `Role` or `UserStatus` (used across auth, RBAC, and
eventually Compass's capability registry), these enums belong to the Job
domain alone. Keeping them local is what "the Job domain must remain
independent" means in practice — no other module needs to import them,
and Job doesn't need to import anything from core beyond the DB base.

Status lifecycle (linear, no skipping, no going backward):

    DRAFT -> OPEN -> CLOSED -> ARCHIVED

Enforced twice, mirroring the Slice 1 pattern:
  - DB layer: `ck_jobs_status_valid` CHECK constraint (valid values only;
    the DB does not encode the transition graph, only membership).
  - Service layer: `JobService._validate_transition` is where the
    transition graph itself lives — see app/services/job_service.py.
"""

import uuid
from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.company import Company
    from app.models.user import User


class JobStatus(StrEnum):
    DRAFT = "draft"
    OPEN = "open"
    CLOSED = "closed"
    ARCHIVED = "archived"


class EmploymentType(StrEnum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    INTERNSHIP = "internship"


class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = (
        CheckConstraint(
            "status IN ('draft', 'open', 'closed', 'archived')", name="ck_jobs_status_valid"
        ),
        CheckConstraint(
            "employment_type IN ('full_time', 'part_time', 'contract', 'internship')",
            name="ck_jobs_employment_type_valid",
        ),
        CheckConstraint(
            "salary_min IS NULL OR salary_max IS NULL OR salary_min <= salary_max",
            name="ck_jobs_salary_range_valid",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    employment_type: Mapped[str] = mapped_column(String(20), nullable=False)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    salary_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    salary_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=JobStatus.DRAFT)

    # --- Recruiter-authored scoring criteria (Slice 4) ---
    # These are the OFFICIAL checklist the Resume Intelligence Agent
    # scores against. The free-text `description` above remains
    # available to the agent as context, but per explicit product
    # decision it must never be treated as, or silently converted into,
    # scoring criteria — only these three fields are. See
    # docs/04_slice4_resume_intelligence.md section 1.
    required_skills: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    preferred_skills: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    min_years_experience: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    company: Mapped["Company"] = relationship()
    creator: Mapped["User | None"] = relationship()

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Job id={self.id} title={self.title!r} status={self.status}>"
