"""
Tests for LeaveRequestService's business rules: date-range validation,
overlap prevention, employee resolution, the approve/reject/cancel
review flow, and balance calculation.

Same mocked-repository approach as test_application_service_rules.py /
test_employee_service.py — no live database.
"""

import uuid
from datetime import date
from unittest.mock import AsyncMock

import pytest

from app.core.exceptions import (
    InvalidDateRangeError,
    InvalidLeaveRequestTransitionError,
    LeaveRequestOverlapError,
    NotFoundError,
)
from app.core.roles import AccountType
from app.models.employee import Employee
from app.models.leave_request import LeaveRequest, LeaveRequestStatus, LeaveType
from app.models.user import User
from app.services.leave_request_service import DEFAULT_ANNUAL_LEAVE_DAYS, LeaveRequestService


def _make_employee_user() -> User:
    return User(
        id=uuid.uuid4(),
        company_id=uuid.uuid4(),
        account_type=AccountType.INTERNAL.value,
        email="employee@example.com",
        password_hash="x",
        first_name="Sarah",
        last_name="Lopez",
    )


def _make_employee(*, company_id: uuid.UUID | None = None) -> Employee:
    return Employee(
        id=uuid.uuid4(),
        company_id=company_id or uuid.uuid4(),
        application_id=uuid.uuid4(),
        first_name="Sarah",
        last_name="Lopez",
        email="employee@example.com",
        job_title="Support Engineer",
        hire_date=date(2026, 1, 1),
    )


def _make_leave_request(
    *,
    employee_id: uuid.UUID,
    status: LeaveRequestStatus = LeaveRequestStatus.PENDING,
    start_date: date = date(2026, 3, 10),
    end_date: date = date(2026, 3, 14),
) -> LeaveRequest:
    return LeaveRequest(
        id=uuid.uuid4(),
        employee_id=employee_id,
        company_id=uuid.uuid4(),
        start_date=start_date,
        end_date=end_date,
        leave_type=LeaveType.VACATION.value,
        status=status.value,
    )


def _make_service(
    *,
    employee: Employee | None,
    has_overlap: bool = False,
    leave_request: LeaveRequest | None = None,
    approved_in_year: list[LeaveRequest] | None = None,
):
    employee_repo = AsyncMock()
    employee_repo.get_by_user_id.return_value = employee

    leave_request_repo = AsyncMock()
    leave_request_repo.has_overlap.return_value = has_overlap
    leave_request_repo.create.side_effect = lambda lr: lr
    leave_request_repo.get_by_id_for_employee.return_value = leave_request
    leave_request_repo.get_by_id_for_company.return_value = leave_request
    leave_request_repo.list_approved_in_year.return_value = approved_in_year or []

    db = AsyncMock()

    service = LeaveRequestService(
        db, leave_request_repository=leave_request_repo, employee_repository=employee_repo
    )
    return service, leave_request_repo, employee_repo


# --- create() ---


async def test_create_succeeds_for_a_valid_non_overlapping_request() -> None:
    employee = _make_employee()
    service, leave_request_repo, _ = _make_service(employee=employee, has_overlap=False)
    user = _make_employee_user()

    leave_request = await service.create(
        acting_user=user,
        start_date=date(2026, 4, 1),
        end_date=date(2026, 4, 5),
        leave_type=LeaveType.VACATION,
        reason="Family trip",
    )

    assert leave_request.employee_id == employee.id
    assert leave_request.company_id == employee.company_id
    assert leave_request.status == LeaveRequestStatus.PENDING.value
    leave_request_repo.create.assert_called_once()


async def test_create_rejects_end_date_before_start_date() -> None:
    employee = _make_employee()
    service, leave_request_repo, _ = _make_service(employee=employee)
    user = _make_employee_user()

    with pytest.raises(InvalidDateRangeError):
        await service.create(
            acting_user=user,
            start_date=date(2026, 4, 5),
            end_date=date(2026, 4, 1),
            leave_type=LeaveType.VACATION,
            reason=None,
        )

    leave_request_repo.has_overlap.assert_not_called()
    leave_request_repo.create.assert_not_called()


async def test_create_rejects_overlapping_request() -> None:
    employee = _make_employee()
    service, leave_request_repo, _ = _make_service(employee=employee, has_overlap=True)
    user = _make_employee_user()

    with pytest.raises(LeaveRequestOverlapError):
        await service.create(
            acting_user=user,
            start_date=date(2026, 4, 1),
            end_date=date(2026, 4, 5),
            leave_type=LeaveType.SICK,
            reason=None,
        )

    leave_request_repo.create.assert_not_called()


async def test_create_raises_not_found_when_user_has_no_employee_record() -> None:
    service, leave_request_repo, _ = _make_service(employee=None)
    user = _make_employee_user()

    with pytest.raises(NotFoundError):
        await service.create(
            acting_user=user,
            start_date=date(2026, 4, 1),
            end_date=date(2026, 4, 5),
            leave_type=LeaveType.PERSONAL,
            reason=None,
        )

    leave_request_repo.has_overlap.assert_not_called()


# --- cancel_mine() ---


async def test_cancel_mine_succeeds_for_a_pending_request() -> None:
    employee = _make_employee()
    leave_request = _make_leave_request(employee_id=employee.id)
    service, _, _ = _make_service(employee=employee, leave_request=leave_request)
    user = _make_employee_user()

    result = await service.cancel_mine(acting_user=user, leave_request_id=leave_request.id)

    assert result.status == LeaveRequestStatus.CANCELLED.value


async def test_cancel_mine_raises_not_found_for_someone_elses_request() -> None:
    employee = _make_employee()
    service, _, _ = _make_service(employee=employee, leave_request=None)
    user = _make_employee_user()

    with pytest.raises(NotFoundError):
        await service.cancel_mine(acting_user=user, leave_request_id=uuid.uuid4())


async def test_cancel_mine_rejects_already_approved_request() -> None:
    employee = _make_employee()
    leave_request = _make_leave_request(
        employee_id=employee.id, status=LeaveRequestStatus.APPROVED
    )
    service, _, _ = _make_service(employee=employee, leave_request=leave_request)
    user = _make_employee_user()

    with pytest.raises(InvalidLeaveRequestTransitionError):
        await service.cancel_mine(acting_user=user, leave_request_id=leave_request.id)


async def test_cancel_mine_does_not_touch_reviewed_by() -> None:
    employee = _make_employee()
    leave_request = _make_leave_request(employee_id=employee.id)
    service, _, _ = _make_service(employee=employee, leave_request=leave_request)
    user = _make_employee_user()

    result = await service.cancel_mine(acting_user=user, leave_request_id=leave_request.id)

    assert result.reviewed_by is None
    assert result.reviewed_at is None


# --- approve() / reject() ---


async def test_approve_sets_status_and_reviewer() -> None:
    employee = _make_employee()
    leave_request = _make_leave_request(employee_id=employee.id)
    service, _, _ = _make_service(employee=employee, leave_request=leave_request)
    admin = _make_employee_user()

    result = await service.approve(acting_user=admin, leave_request_id=leave_request.id)

    assert result.status == LeaveRequestStatus.APPROVED.value
    assert result.reviewed_by == admin.id
    assert result.reviewed_at is not None


async def test_reject_sets_status_and_reviewer() -> None:
    employee = _make_employee()
    leave_request = _make_leave_request(employee_id=employee.id)
    service, _, _ = _make_service(employee=employee, leave_request=leave_request)
    admin = _make_employee_user()

    result = await service.reject(acting_user=admin, leave_request_id=leave_request.id)

    assert result.status == LeaveRequestStatus.REJECTED.value
    assert result.reviewed_by == admin.id


async def test_approve_raises_not_found_for_cross_company_request() -> None:
    employee = _make_employee()
    service, _, _ = _make_service(employee=employee, leave_request=None)
    admin = _make_employee_user()

    with pytest.raises(NotFoundError):
        await service.approve(acting_user=admin, leave_request_id=uuid.uuid4())


async def test_cannot_approve_an_already_approved_request() -> None:
    employee = _make_employee()
    leave_request = _make_leave_request(
        employee_id=employee.id, status=LeaveRequestStatus.APPROVED
    )
    service, _, _ = _make_service(employee=employee, leave_request=leave_request)
    admin = _make_employee_user()

    with pytest.raises(InvalidLeaveRequestTransitionError):
        await service.approve(acting_user=admin, leave_request_id=leave_request.id)


async def test_cannot_reject_a_cancelled_request() -> None:
    employee = _make_employee()
    leave_request = _make_leave_request(
        employee_id=employee.id, status=LeaveRequestStatus.CANCELLED
    )
    service, _, _ = _make_service(employee=employee, leave_request=leave_request)
    admin = _make_employee_user()

    with pytest.raises(InvalidLeaveRequestTransitionError):
        await service.reject(acting_user=admin, leave_request_id=leave_request.id)


# --- get_balance() ---


async def test_balance_with_no_approved_requests_is_the_full_allotment() -> None:
    employee = _make_employee()
    service, _, _ = _make_service(employee=employee, approved_in_year=[])
    user = _make_employee_user()

    balance = await service.get_balance(acting_user=user, year=2026)

    assert balance.annual_allotment == DEFAULT_ANNUAL_LEAVE_DAYS
    assert balance.days_used == 0
    assert balance.days_remaining == DEFAULT_ANNUAL_LEAVE_DAYS


async def test_balance_counts_calendar_days_inclusive_of_both_endpoints() -> None:
    employee = _make_employee()
    # March 10 through March 14 inclusive = 5 days, not 4.
    approved = [
        _make_leave_request(
            employee_id=employee.id,
            status=LeaveRequestStatus.APPROVED,
            start_date=date(2026, 3, 10),
            end_date=date(2026, 3, 14),
        )
    ]
    service, _, _ = _make_service(employee=employee, approved_in_year=approved)
    user = _make_employee_user()

    balance = await service.get_balance(acting_user=user, year=2026)

    assert balance.days_used == 5
    assert balance.days_remaining == DEFAULT_ANNUAL_LEAVE_DAYS - 5


async def test_balance_sums_multiple_approved_requests() -> None:
    employee = _make_employee()
    approved = [
        _make_leave_request(
            employee_id=employee.id,
            status=LeaveRequestStatus.APPROVED,
            start_date=date(2026, 1, 5),
            end_date=date(2026, 1, 6),  # 2 days
        ),
        _make_leave_request(
            employee_id=employee.id,
            status=LeaveRequestStatus.APPROVED,
            start_date=date(2026, 6, 1),
            end_date=date(2026, 6, 10),  # 10 days
        ),
    ]
    service, _, _ = _make_service(employee=employee, approved_in_year=approved)
    user = _make_employee_user()

    balance = await service.get_balance(acting_user=user, year=2026)

    assert balance.days_used == 12
    assert balance.days_remaining == DEFAULT_ANNUAL_LEAVE_DAYS - 12


async def test_balance_can_go_negative_when_admin_over_approves() -> None:
    employee = _make_employee()
    approved = [
        _make_leave_request(
            employee_id=employee.id,
            status=LeaveRequestStatus.APPROVED,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),  # 31 days, exceeds the 20-day allotment
        )
    ]
    service, _, _ = _make_service(employee=employee, approved_in_year=approved)
    user = _make_employee_user()

    balance = await service.get_balance(acting_user=user, year=2026)

    assert balance.days_used == 31
    assert balance.days_remaining == DEFAULT_ANNUAL_LEAVE_DAYS - 31
    assert balance.days_remaining < 0
