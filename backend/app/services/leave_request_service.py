"""
LeaveRequestService.

Sub-slice 9c (Leave Management), V2 Employee Portal.

Owns every business rule around leave requests: submitting one,
reading them (employee's own, or a company's approval queue), and
moving one through its status lifecycle. Same independence discipline
as JobService/ApplicationService — no Workflow Engine, no Compass, no
Agent anywhere in this file.

Status lifecycle (PENDING is the only non-terminal state):

    PENDING -> APPROVED   (admin/hiring manager)
    PENDING -> REJECTED   (admin/hiring manager)
    PENDING -> CANCELLED  (employee, own request only)

Enforced the same two-layer way as every other lifecycle in this
codebase: the DB CHECK constrains valid status VALUES only;
`_validate_transition` here is the only place the transition GRAPH is
encoded. Note this graph is intentionally NOT keyed by "who is asking"
— `approve`/`reject`/`cancel_mine` each call the same
`_validate_transition`, and it's the API layer's RBAC gating
(`require_roles`) that decides which caller may reach which method,
not the state machine itself. This mirrors ApplicationService's
`transition_status`, which likewise doesn't encode "only a recruiter
may move SCREENING -> INTERVIEW" in the graph itself.

Approval routing: per confirmed product decision, there is no manager
hierarchy anywhere in this codebase (Employee has no manager_id, no
Department concept). Approval is company-wide — any user holding
Role.ADMIN or Role.HIRING_MANAGER at the same company may approve or
reject any pending request. That's enforced entirely by RBAC + company
scoping (`get_by_id_for_company`), not by anything in this file that
looks at "whose request this is."
"""

import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    InvalidDateRangeError,
    InvalidLeaveRequestTransitionError,
    LeaveRequestOverlapError,
    NotFoundError,
)
from app.models.employee import Employee
from app.models.leave_request import LeaveRequest, LeaveRequestStatus, LeaveType
from app.models.user import User
from app.repositories.employee_repository import EmployeeRepository
from app.repositories.leave_request_repository import LeaveRequestRepository

#: Fixed annual allotment for the MVP — confirmed simplification, no
#: per-employee or per-company override, no accrual, no carry-over.
#: Calendar-day counting (inclusive of both endpoints), not
#: business-day-aware — see module docstring on the confirmed scope.
DEFAULT_ANNUAL_LEAVE_DAYS = 20


@dataclass(frozen=True)
class LeaveBalance:
    year: int
    annual_allotment: int
    days_used: int
    days_remaining: int

# The entire transition graph. PENDING is the only non-terminal state;
# APPROVED, REJECTED, and CANCELLED all have no outgoing transitions —
# once a decision is made (by an admin) or the employee withdraws their
# own request, that's final for the MVP. No "un-cancel" or "re-open a
# rejected request" flow exists.
_ALLOWED_TRANSITIONS: dict[LeaveRequestStatus, set[LeaveRequestStatus]] = {
    LeaveRequestStatus.PENDING: {
        LeaveRequestStatus.APPROVED,
        LeaveRequestStatus.REJECTED,
        LeaveRequestStatus.CANCELLED,
    },
    LeaveRequestStatus.APPROVED: set(),
    LeaveRequestStatus.REJECTED: set(),
    LeaveRequestStatus.CANCELLED: set(),
}


class LeaveRequestService:
    def __init__(
        self,
        db: AsyncSession,
        leave_request_repository: LeaveRequestRepository | None = None,
        employee_repository: EmployeeRepository | None = None,
    ) -> None:
        self._db = db
        self._leave_requests = leave_request_repository or LeaveRequestRepository(db)
        self._employees = employee_repository or EmployeeRepository(db)

    # --- Employee-facing (portal self-service) ---

    async def create(
        self,
        *,
        acting_user: User,
        start_date: date,
        end_date: date,
        leave_type: LeaveType,
        reason: str | None,
    ) -> LeaveRequest:
        employee = await self._resolve_employee(acting_user)
        self._assert_valid_date_range(start_date, end_date)

        overlaps = await self._leave_requests.has_overlap(employee.id, start_date, end_date)
        if overlaps:
            raise LeaveRequestOverlapError(
                "This date range overlaps an existing pending or approved leave request."
            )

        leave_request = LeaveRequest(
            employee_id=employee.id,
            company_id=employee.company_id,
            start_date=start_date,
            end_date=end_date,
            leave_type=leave_type.value,
            reason=reason,
            status=LeaveRequestStatus.PENDING.value,
        )
        leave_request = await self._leave_requests.create(leave_request)
        await self._db.commit()
        return leave_request

    async def list_mine(
        self, *, acting_user: User, page: int, page_size: int
    ) -> tuple[list[LeaveRequest], int]:
        employee = await self._resolve_employee(acting_user)
        return await self._leave_requests.list_for_employee(
            employee.id, page=page, page_size=page_size
        )

    async def get_balance(
        self, *, acting_user: User, year: int | None = None
    ) -> LeaveBalance:
        """
        Returns the employee's remaining balance for `year` (defaulting
        to the current calendar year). `days_used` sums calendar days
        (inclusive of both endpoints) across every APPROVED request
        whose start_date falls in that year — PENDING requests don't
        count against the balance yet, only decided ones. Deliberately
        does not clamp `days_remaining` at zero: an admin can approve a
        request that pushes an employee over their allotment (this
        service never blocks that), and a negative remaining balance is
        the honest way to surface that it happened rather than hiding
        it behind a floor of zero.
        """
        employee = await self._resolve_employee(acting_user)
        target_year = year or datetime.now(UTC).date().year

        approved = await self._leave_requests.list_approved_in_year(employee.id, target_year)
        days_used = sum((r.end_date - r.start_date).days + 1 for r in approved)

        return LeaveBalance(
            year=target_year,
            annual_allotment=DEFAULT_ANNUAL_LEAVE_DAYS,
            days_used=days_used,
            days_remaining=DEFAULT_ANNUAL_LEAVE_DAYS - days_used,
        )

    async def cancel_mine(
        self, *, acting_user: User, leave_request_id: uuid.UUID
    ) -> LeaveRequest:
        employee = await self._resolve_employee(acting_user)
        leave_request = await self._leave_requests.get_by_id_for_employee(
            leave_request_id, employee.id
        )
        if leave_request is None:
            raise NotFoundError("Leave request not found.")

        current_status = LeaveRequestStatus(leave_request.status)
        self._validate_transition(current_status, LeaveRequestStatus.CANCELLED)

        leave_request.status = LeaveRequestStatus.CANCELLED.value
        await self._db.commit()
        return leave_request

    # --- Admin/hiring-manager-facing (approval queue) ---

    async def list_for_company(
        self,
        *,
        acting_user: User,
        status: str | None,
        page: int,
        page_size: int,
    ) -> tuple[list[LeaveRequest], int]:
        return await self._leave_requests.list_for_company(
            acting_user.company_id, status=status, page=page, page_size=page_size
        )

    async def approve(
        self, *, acting_user: User, leave_request_id: uuid.UUID
    ) -> LeaveRequest:
        return await self._review(
            acting_user=acting_user,
            leave_request_id=leave_request_id,
            target_status=LeaveRequestStatus.APPROVED,
        )

    async def reject(
        self, *, acting_user: User, leave_request_id: uuid.UUID
    ) -> LeaveRequest:
        return await self._review(
            acting_user=acting_user,
            leave_request_id=leave_request_id,
            target_status=LeaveRequestStatus.REJECTED,
        )

    async def _review(
        self,
        *,
        acting_user: User,
        leave_request_id: uuid.UUID,
        target_status: LeaveRequestStatus,
    ) -> LeaveRequest:
        leave_request = await self._leave_requests.get_by_id_for_company(
            leave_request_id, acting_user.company_id
        )
        if leave_request is None:
            raise NotFoundError("Leave request not found.")

        current_status = LeaveRequestStatus(leave_request.status)
        self._validate_transition(current_status, target_status)

        leave_request.status = target_status.value
        leave_request.reviewed_by = acting_user.id
        leave_request.reviewed_at = datetime.now(UTC)
        await self._db.commit()
        return leave_request

    # --- Shared internals ---

    async def _resolve_employee(self, user: User) -> Employee:
        """
        Resolves the calling user's Employee row. Raises NotFoundError
        (not AuthorizationError) for the same reason cross-company
        Application/Job access does — a Role.EMPLOYEE account without a
        linked Employee row shouldn't get a different error shape that
        hints at *why* it's missing.
        """
        employee = await self._employees.get_by_user_id(user.id)
        if employee is None:
            raise NotFoundError("No employee record found for this account.")
        return employee

    @staticmethod
    def _validate_transition(
        current: LeaveRequestStatus, target: LeaveRequestStatus
    ) -> None:
        allowed = _ALLOWED_TRANSITIONS.get(current, set())
        if target not in allowed:
            raise InvalidLeaveRequestTransitionError(
                f"Cannot transition a leave request from '{current.value}' to '{target.value}'."
            )

    @staticmethod
    def _assert_valid_date_range(start_date: date, end_date: date) -> None:
        # Defense in depth — ck_leave_requests_date_range_valid enforces
        # this at the DB layer too; this is the service-layer half, so
        # the failure is a clean domain error rather than a raw
        # IntegrityError bubbling out of the database driver.
        if end_date < start_date:
            raise InvalidDateRangeError("end_date must not be before start_date.")
