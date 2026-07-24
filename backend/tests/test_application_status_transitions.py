"""
Tests for ApplicationService's status transition state machine.

Same shape as tests/test_job_status_transitions.py: `_validate_transition`
is a pure staticmethod, so the full transition graph — including the
REJECTED branch reachable from four different states, and two distinct
terminal states — is tested with zero database.
"""

import itertools

import pytest

from app.core.exceptions import InvalidApplicationStatusTransitionError
from app.models.application import ApplicationStatus
from app.services.application_service import ApplicationService

VALID_TRANSITIONS = [
    (ApplicationStatus.APPLIED, ApplicationStatus.SCREENING),
    (ApplicationStatus.SCREENING, ApplicationStatus.INTERVIEW),
    (ApplicationStatus.INTERVIEW, ApplicationStatus.OFFER),
    (ApplicationStatus.OFFER, ApplicationStatus.HIRED),
    (ApplicationStatus.APPLIED, ApplicationStatus.REJECTED),
    (ApplicationStatus.SCREENING, ApplicationStatus.REJECTED),
    (ApplicationStatus.INTERVIEW, ApplicationStatus.REJECTED),
    (ApplicationStatus.OFFER, ApplicationStatus.REJECTED),
]


@pytest.mark.parametrize("current,target", VALID_TRANSITIONS)
def test_valid_transitions_are_accepted(
    current: ApplicationStatus, target: ApplicationStatus
) -> None:
    ApplicationService._validate_transition(current, target)  # does not raise


def _all_invalid_pairs():
    all_pairs = set(itertools.product(ApplicationStatus, ApplicationStatus))
    return sorted(all_pairs - set(VALID_TRANSITIONS), key=lambda p: (p[0].value, p[1].value))


@pytest.mark.parametrize("current,target", _all_invalid_pairs())
def test_invalid_transitions_are_rejected(
    current: ApplicationStatus, target: ApplicationStatus
) -> None:
    with pytest.raises(InvalidApplicationStatusTransitionError):
        ApplicationService._validate_transition(current, target)


def test_cannot_skip_screening() -> None:
    with pytest.raises(InvalidApplicationStatusTransitionError):
        ApplicationService._validate_transition(
            ApplicationStatus.APPLIED, ApplicationStatus.INTERVIEW
        )


def test_cannot_skip_straight_to_hired() -> None:
    with pytest.raises(InvalidApplicationStatusTransitionError):
        ApplicationService._validate_transition(ApplicationStatus.APPLIED, ApplicationStatus.HIRED)


def test_cannot_move_backward_from_interview_to_screening() -> None:
    with pytest.raises(InvalidApplicationStatusTransitionError):
        ApplicationService._validate_transition(
            ApplicationStatus.INTERVIEW, ApplicationStatus.SCREENING
        )


def test_rejected_is_reachable_from_every_non_terminal_state() -> None:
    for status in (
        ApplicationStatus.APPLIED,
        ApplicationStatus.SCREENING,
        ApplicationStatus.INTERVIEW,
        ApplicationStatus.OFFER,
    ):
        ApplicationService._validate_transition(status, ApplicationStatus.REJECTED)  # no raise


def test_hired_is_terminal() -> None:
    for target in ApplicationStatus:
        with pytest.raises(InvalidApplicationStatusTransitionError):
            ApplicationService._validate_transition(ApplicationStatus.HIRED, target)


def test_rejected_is_terminal() -> None:
    for target in ApplicationStatus:
        with pytest.raises(InvalidApplicationStatusTransitionError):
            ApplicationService._validate_transition(ApplicationStatus.REJECTED, target)


def test_no_self_transitions() -> None:
    for status in ApplicationStatus:
        with pytest.raises(InvalidApplicationStatusTransitionError):
            ApplicationService._validate_transition(status, status)


def test_cannot_reject_a_hired_application() -> None:
    with pytest.raises(InvalidApplicationStatusTransitionError):
        ApplicationService._validate_transition(
            ApplicationStatus.HIRED, ApplicationStatus.REJECTED
        )
