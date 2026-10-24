"""
Tests for JobService's status transition state machine.

`_validate_transition` is a pure staticmethod — same pattern as Slice
1's `AuthService._assert_company_assignment_valid` — so the entire
transition graph (DRAFT -> OPEN -> CLOSED -> ARCHIVED, linear, no
skipping, no backward moves) is tested with zero database, zero mocking.
"""

import itertools

import pytest

from app.core.exceptions import InvalidJobStatusTransitionError
from app.models.job import JobStatus
from app.services.job_service import JobService

VALID_TRANSITIONS = [
    (JobStatus.DRAFT, JobStatus.OPEN),
    (JobStatus.OPEN, JobStatus.CLOSED),
    (JobStatus.CLOSED, JobStatus.ARCHIVED),
]


@pytest.mark.parametrize("current,target", VALID_TRANSITIONS)
def test_valid_transitions_are_accepted(current: JobStatus, target: JobStatus) -> None:
    JobService._validate_transition(current, target)  # does not raise


def _all_invalid_pairs():
    """Every (current, target) pair NOT in VALID_TRANSITIONS, including no-ops."""
    all_pairs = set(itertools.product(JobStatus, JobStatus))
    return sorted(all_pairs - set(VALID_TRANSITIONS), key=lambda p: (p[0].value, p[1].value))


@pytest.mark.parametrize("current,target", _all_invalid_pairs())
def test_invalid_transitions_are_rejected(current: JobStatus, target: JobStatus) -> None:
    with pytest.raises(InvalidJobStatusTransitionError):
        JobService._validate_transition(current, target)


def test_cannot_skip_from_draft_to_closed() -> None:
    with pytest.raises(InvalidJobStatusTransitionError):
        JobService._validate_transition(JobStatus.DRAFT, JobStatus.CLOSED)


def test_cannot_skip_from_draft_to_archived() -> None:
    with pytest.raises(InvalidJobStatusTransitionError):
        JobService._validate_transition(JobStatus.DRAFT, JobStatus.ARCHIVED)


def test_cannot_move_backward_from_closed_to_open() -> None:
    with pytest.raises(InvalidJobStatusTransitionError):
        JobService._validate_transition(JobStatus.CLOSED, JobStatus.OPEN)


def test_archived_is_terminal() -> None:
    for target in JobStatus:
        with pytest.raises(InvalidJobStatusTransitionError):
            JobService._validate_transition(JobStatus.ARCHIVED, target)


def test_no_self_transitions() -> None:
    for status in JobStatus:
        with pytest.raises(InvalidJobStatusTransitionError):
            JobService._validate_transition(status, status)
