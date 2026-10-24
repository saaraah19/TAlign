"""
Approving, rejecting and cancelling a leave request must hand back a
RELOADED request, not the instance that was just modified.

Regression: against a real database every approve and reject returned a
500. The service changed the row and committed; the UPDATE made SQLAlchemy
discard the database-generated `updated_at`, and the route's response
model then read it — which async SQLAlchemy cannot lazy-load
(MissingGreenlet). Mocked tests never showed it. The contract that
prevents it, tested here: after committing, the service re-fetches.
"""

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.models.leave_request import LeaveRequestStatus
from app.services.leave_request_service import LeaveRequestService

COMPANY_ID = uuid.uuid4()
REQUEST_ID = uuid.uuid4()


def _setup() -> tuple[LeaveRequestService, list[str], SimpleNamespace, SimpleNamespace]:
    calls: list[str] = []
    stale = SimpleNamespace(
        id=REQUEST_ID, status=LeaveRequestStatus.PENDING.value, reviewed_by=None, reviewed_at=None
    )
    reloaded = SimpleNamespace(id=REQUEST_ID, status="(reloaded copy)")

    db = AsyncMock()

    async def commit() -> None:
        calls.append("commit")

    db.commit = commit

    async def load(*_args: object) -> SimpleNamespace:
        # First call: the lookup before the change. Later calls: the reload.
        calls.append("load")
        return stale if calls.count("load") == 1 else reloaded

    leave_requests = AsyncMock()
    leave_requests.get_by_id_for_company = load
    leave_requests.get_by_id_for_employee = load

    employees = AsyncMock()
    employees.get_by_user_id.return_value = SimpleNamespace(id=uuid.uuid4())

    service = LeaveRequestService(
        db, leave_request_repository=leave_requests, employee_repository=employees
    )
    return service, calls, stale, reloaded


def _admin() -> SimpleNamespace:
    return SimpleNamespace(id=uuid.uuid4(), company_id=COMPANY_ID)


@pytest.mark.parametrize("action", ["approve", "reject"])
async def test_review_returns_a_reloaded_request_after_committing(action: str) -> None:
    service, calls, stale, reloaded = _setup()

    result = await getattr(service, action)(acting_user=_admin(), leave_request_id=REQUEST_ID)

    assert result is reloaded
    assert result is not stale
    assert calls == ["load", "commit", "load"]  # look up, change + commit, then reload


async def test_review_still_records_who_decided_and_when() -> None:
    service, _, stale, _ = _setup()
    reviewer = _admin()

    await service.approve(acting_user=reviewer, leave_request_id=REQUEST_ID)

    assert stale.status == LeaveRequestStatus.APPROVED.value
    assert stale.reviewed_by == reviewer.id
    assert stale.reviewed_at is not None


async def test_cancel_returns_a_reloaded_request_after_committing() -> None:
    service, calls, stale, reloaded = _setup()

    result = await service.cancel_mine(acting_user=_admin(), leave_request_id=REQUEST_ID)

    assert result is reloaded
    assert result is not stale
    assert stale.status == LeaveRequestStatus.CANCELLED.value
    assert calls == ["load", "commit", "load"]
