"""
Tests for LeaveRequestService's status transition state machine.

Same shape as tests/test_application_status_transitions.py:
`_validate_transition` is a pure staticmethod, so the full transition
graph is tested with zero database. PENDING is the only non-terminal
state; APPROVED, REJECTED, and CANCELLED all have no outgoing
transitions.
"""

import itertools

import pytest

from app.core.exceptions import InvalidLeaveRequestTransitionError
from app.models.leave_request import LeaveRequestStatus
from app.services.leave_request_service import LeaveRequestService

VALID_TRANSITIONS = [
    (LeaveRequestStatus.PENDING, LeaveRequestStatus.APPROVED),
    (LeaveRequestStatus.PENDING, LeaveRequestStatus.REJECTED),
    (LeaveRequestStatus.PENDING, LeaveRequestStatus.CANCELLED),
]


@pytest.mark.parametrize("current,target", VALID_TRANSITIONS)
def test_valid_transitions_are_accepted(
    current: LeaveRequestStatus, target: LeaveRequestStatus
) -> None:
    LeaveRequestService._validate_transition(current, target)  # does not raise


def _all_invalid_pairs():
    all_pairs = set(itertools.product(LeaveRequestStatus, LeaveRequestStatus))
    return sorted(all_pairs - set(VALID_TRANSITIONS), key=lambda p: (p[0].value, p[1].value))


@pytest.mark.parametrize("current,target", _all_invalid_pairs())
def test_invalid_transitions_are_rejected(
    current: LeaveRequestStatus, target: LeaveRequestStatus
) -> None:
    with pytest.raises(InvalidLeaveRequestTransitionError):
        LeaveRequestService._validate_transition(current, target)


def test_no_self_transitions() -> None:
    for status in LeaveRequestStatus:
        with pytest.raises(InvalidLeaveRequestTransitionError):
            LeaveRequestService._validate_transition(status, status)


def test_approved_is_terminal() -> None:
    for target in LeaveRequestStatus:
        with pytest.raises(InvalidLeaveRequestTransitionError):
            LeaveRequestService._validate_transition(LeaveRequestStatus.APPROVED, target)


def test_rejected_is_terminal() -> None:
    for target in LeaveRequestStatus:
        with pytest.raises(InvalidLeaveRequestTransitionError):
            LeaveRequestService._validate_transition(LeaveRequestStatus.REJECTED, target)


def test_cancelled_is_terminal() -> None:
    for target in LeaveRequestStatus:
        with pytest.raises(InvalidLeaveRequestTransitionError):
            LeaveRequestService._validate_transition(LeaveRequestStatus.CANCELLED, target)


def test_cannot_uncancel() -> None:
    with pytest.raises(InvalidLeaveRequestTransitionError):
        LeaveRequestService._validate_transition(
            LeaveRequestStatus.CANCELLED, LeaveRequestStatus.PENDING
        )


def test_cannot_reopen_a_rejected_request() -> None:
    with pytest.raises(InvalidLeaveRequestTransitionError):
        LeaveRequestService._validate_transition(
            LeaveRequestStatus.REJECTED, LeaveRequestStatus.PENDING
        )
