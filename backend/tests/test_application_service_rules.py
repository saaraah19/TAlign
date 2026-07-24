"""
Tests for ApplicationService.apply()'s business rules: duplicate
detection, job-must-be-open, and candidate-account validation.

These require I/O (checking whether an application already exists,
fetching the job) so they can't be pure staticmethod tests like
test_application_status_transitions.py. Instead, ApplicationService's
constructor accepts injected repositories specifically for this —
see app/services/application_service.py's __init__. Everything here
runs with mocked repositories and a mocked AsyncSession; no live
database, no docker-compose, no pytest-asyncio fixtures beyond the
plain async test functions this project already uses.
"""

import uuid
from unittest.mock import AsyncMock

import pytest

from app.core.exceptions import (
    DuplicateApplicationError,
    InvalidCandidateError,
    JobNotOpenForApplicationsError,
)
from app.core.roles import AccountType
from app.models.job import Job, JobStatus
from app.models.user import User
from app.services.application_service import ApplicationService


def _make_candidate() -> User:
    return User(
        id=uuid.uuid4(),
        company_id=None,
        account_type=AccountType.CANDIDATE.value,
        email="candidate@example.com",
        password_hash="x",
        first_name="Ada",
        last_name="Lovelace",
    )


def _make_internal_user() -> User:
    return User(
        id=uuid.uuid4(),
        company_id=uuid.uuid4(),
        account_type=AccountType.INTERNAL.value,
        email="recruiter@example.com",
        password_hash="x",
        first_name="Emma",
        last_name="Martin",
    )


def _make_open_job(company_id: uuid.UUID | None = None) -> Job:
    return Job(
        id=uuid.uuid4(),
        company_id=company_id or uuid.uuid4(),
        title="Backend Engineer",
        description="...",
        employment_type="full_time",
        status=JobStatus.OPEN.value,
    )


def _make_service(*, job: Job | None, already_applied: bool) -> ApplicationService:
    application_repo = AsyncMock()
    application_repo.exists_for_candidate_and_job.return_value = already_applied
    application_repo.create.side_effect = lambda app: app

    job_repo = AsyncMock()
    job_repo.get_by_id.return_value = job

    db = AsyncMock()

    return ApplicationService(
        db, application_repository=application_repo, job_repository=job_repo
    )


async def test_apply_succeeds_for_open_job_and_new_candidate() -> None:
    job = _make_open_job()
    service = _make_service(job=job, already_applied=False)
    candidate = _make_candidate()

    application = await service.apply(candidate=candidate, job_id=job.id)

    assert application.candidate_id == candidate.id
    assert application.job_id == job.id
    assert application.company_id == job.company_id
    assert application.status == "applied"


async def test_apply_rejects_duplicate_application() -> None:
    job = _make_open_job()
    service = _make_service(job=job, already_applied=True)
    candidate = _make_candidate()

    with pytest.raises(DuplicateApplicationError):
        await service.apply(candidate=candidate, job_id=job.id)


async def test_apply_rejects_job_that_is_not_open() -> None:
    job = _make_open_job()
    job.status = JobStatus.DRAFT.value
    service = _make_service(job=job, already_applied=False)
    candidate = _make_candidate()

    with pytest.raises(JobNotOpenForApplicationsError):
        await service.apply(candidate=candidate, job_id=job.id)


async def test_apply_rejects_closed_job() -> None:
    job = _make_open_job()
    job.status = JobStatus.CLOSED.value
    service = _make_service(job=job, already_applied=False)
    candidate = _make_candidate()

    with pytest.raises(JobNotOpenForApplicationsError):
        await service.apply(candidate=candidate, job_id=job.id)


async def test_apply_rejects_non_candidate_account() -> None:
    job = _make_open_job()
    service = _make_service(job=job, already_applied=False)
    internal_user = _make_internal_user()

    with pytest.raises(InvalidCandidateError):
        await service.apply(candidate=internal_user, job_id=job.id)


async def test_apply_checks_candidate_validity_before_touching_the_database() -> None:
    """
    An invalid candidate should be rejected before any repository call —
    not merely before the write, but before the read too. This matters
    because a job lookup by an unauthenticated/invalid caller is itself
    unnecessary I/O once RBAC has already failed the request in
    principle; the service shouldn't rely solely on the API layer's RBAC
    guard having run first.
    """
    application_repo = AsyncMock()
    job_repo = AsyncMock()
    db = AsyncMock()
    service = ApplicationService(
        db, application_repository=application_repo, job_repository=job_repo
    )
    internal_user = _make_internal_user()

    with pytest.raises(InvalidCandidateError):
        await service.apply(candidate=internal_user, job_id=uuid.uuid4())

    job_repo.get_by_id.assert_not_called()
    application_repo.exists_for_candidate_and_job.assert_not_called()
