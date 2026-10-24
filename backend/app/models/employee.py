"""
Employee model.

Deliberately thin for Slice 7's MVP scope — this is NOT the Employee
Portal (leave, payroll, self-service, documents are all V2, per
CLAUDE.md's locked scope). It exists purely so the Workflow Engine's
"candidate hired" workflow has something real and inspectable to create,
rather than a hollow no-op step.

`user_id` is nullable and, in this MVP, always NULL — no login account
or authentication is created for a new employee. The column exists as a
deliberate hook for a future V2 slice (Employee Portal self-service
login), not because anything in this slice populates it. Documenting
this explicitly here so a future reader doesn't mistake the always-NULL
value for a bug.

`application_id` is unique (not just indexed) — this is the load-bearing
column for hire-workflow idempotency. `EmployeeService` checks for an
existing Employee by `application_id` before creating one; the DB
UNIQUE constraint is the second layer of that same guarantee, same
two-layer discipline as every other invariant in this codebase (see
uq_applications_candidate_job for the precedent).

`status` has exactly one value for the MVP (`ACTIVE`) — no offboarding
flow exists yet. Modeled as a string column with a CHECK constraint
now anyway, matching the two-layer-validation convention used
everywhere else, so adding OFFBOARDED later doesn't require introducing
the pattern from scratch.
"""

import uuid
from datetime import date, datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.application import Application
    from app.models.company import Company
    from app.models.user import User


class EmployeeStatus(StrEnum):
    ACTIVE = "active"


class Employee(Base):
    __tablename__ = "employees"
    __table_args__ = (
        CheckConstraint("status IN ('active')", name="ck_employees_status_valid"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    #: The hire-workflow idempotency key — see module docstring. UNIQUE,
    #: not just a plain FK, so a race between two triggers of the same
    #: hire workflow cannot create two Employee rows for one Application.
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    #: Always NULL in this MVP — see module docstring. Reserved for a
    #: future V2 slice that creates a real login account for the
    #: employee (Employee Portal self-service).
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    job_title: Mapped[str] = mapped_column(String(255), nullable=False)
    hire_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=EmployeeStatus.ACTIVE)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    company: Mapped["Company"] = relationship()
    application: Mapped["Application"] = relationship()
    user: Mapped["User | None"] = relationship()

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Employee id={self.id} name={self.first_name} {self.last_name!r}>"
