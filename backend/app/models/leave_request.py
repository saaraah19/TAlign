"""
LeaveRequest model.

Sub-slice 9c (Leave Management), V2 Employee Portal.

Deliberately simple for the confirmed MVP scope:
  - No manager hierarchy exists anywhere in this codebase (Employee has
    no manager_id, no Department concept) — per explicit product
    decision, approval routes to any ADMIN/HIRING_MANAGER at the
    company collectively, not to a specific individual. See
    LeaveRequestService for where that's enforced (RBAC at the API
    layer, company-scoping at the service layer).
  - Leave balance is a simple fixed annual allotment
    (DEFAULT_ANNUAL_LEAVE_DAYS on LeaveRequestService), calendar-day
    counting (inclusive of both start_date and end_date, weekends
    included) — not business-day-aware. Confirmed simplification.

`company_id` is denormalized from `employee.company_id` at creation
time, same reasoning and same immutability as Application.company_id
being denormalized from Job.company_id (see app/models/application.py's
module docstring) — pure query convenience for company-scoped admin
reads, set once and never a second source of truth since an Employee's
company can never change after creation either.

Status lifecycle — PENDING is the only non-terminal state:

    PENDING -> APPROVED   (admin/hiring manager)
    PENDING -> REJECTED   (admin/hiring manager)
    PENDING -> CANCELLED  (employee, own request only)

APPROVED, REJECTED, and CANCELLED are all terminal — no further
transitions once a request leaves PENDING. Enforced two ways, mirroring
every other lifecycle in this codebase:
  - DB layer: `ck_leave_requests_status_valid` (valid values only).
  - Service layer: `LeaveRequestService._validate_transition` is the
    only place the transition GRAPH is encoded.

Overlap prevention (a new request can't overlap an existing PENDING or
APPROVED request for the same employee) is a service-layer check
against a targeted repository query, not a DB constraint — the range-
overlap condition isn't expressible as a plain CHECK (it depends on
other rows, not just this row's own columns), same reasoning as
Application's duplicate-application check living in the service rather
than the DB (see application.py's module docstring on why candidate
validity isn't a CHECK constraint either). A CANCELLED or REJECTED
request never blocks — only PENDING/APPROVED occupy calendar time.
"""

import uuid
from datetime import date, datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.company import Company
    from app.models.employee import Employee
    from app.models.user import User


class LeaveRequestStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class LeaveType(StrEnum):
    VACATION = "vacation"
    SICK = "sick"
    PERSONAL = "personal"


class LeaveRequest(Base):
    __tablename__ = "leave_requests"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'approved', 'rejected', 'cancelled')",
            name="ck_leave_requests_status_valid",
        ),
        CheckConstraint(
            "leave_type IN ('vacation', 'sick', 'personal')",
            name="ck_leave_requests_leave_type_valid",
        ),
        CheckConstraint(
            "end_date >= start_date",
            name="ck_leave_requests_date_range_valid",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employees.id", ondelete="CASCADE"), nullable=False
    )
    #: Denormalized from employee.company_id at creation — see module
    #: docstring. Never changes afterward.
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )

    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    leave_type: Mapped[str] = mapped_column(String(20), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=LeaveRequestStatus.PENDING
    )

    #: Who approved/rejected this request. NULL while PENDING, and stays
    #: NULL forever for a CANCELLED request (an employee cancelling
    #: their own request never touches this column — see
    #: LeaveRequestService.cancel_mine).
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    employee: Mapped["Employee"] = relationship()
    company: Mapped["Company"] = relationship()
    reviewer: Mapped["User | None"] = relationship()

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<LeaveRequest id={self.id} employee_id={self.employee_id} "
            f"status={self.status}>"
        )
