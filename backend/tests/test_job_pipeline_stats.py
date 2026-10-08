"""Tests for JobService.get_pipeline_stats — the per-job applicant/stage
aggregation added for the Jobs list page redesign."""

import uuid
from unittest.mock import AsyncMock

import pytest

from app.core.exceptions import AuthorizationError
from app.core.roles import AccountType
from app.models.user import User
from app.services.job_service import JobService


def _internal_user(company_id: uuid.UUID) -> User:
    return User(
        id=uuid.uuid4(),
        company_id=company_id,
        account_type=AccountType.INTERNAL.value,
        email="sarah@example.com",
        password_hash="x",
        first_name="Sarah",
        last_name="Lopez",
    )


async def test_get_pipeline_stats_delegates_to_application_repository() -> None:
    company_id = uuid.uuid4()
    job_id = uuid.uuid4()
    application_repo = AsyncMock()
    application_repo.count_by_status_grouped_by_job.return_value = {
        job_id: {"applied": 3, "screening": 1}
    }
    service = JobService(AsyncMock(), application_repository=application_repo)

    stats = await service.get_pipeline_stats(_internal_user(company_id))

    assert stats == {job_id: {"applied": 3, "screening": 1}}
    application_repo.count_by_status_grouped_by_job.assert_awaited_once_with(company_id)


async def test_get_pipeline_stats_requires_an_internal_company_scoped_user() -> None:
    candidate = User(
        id=uuid.uuid4(),
        company_id=None,
        account_type=AccountType.CANDIDATE.value,
        email="candidate@example.com",
        password_hash="x",
        first_name="Ahmed",
        last_name="Benali",
    )
    service = JobService(AsyncMock(), application_repository=AsyncMock())

    with pytest.raises(AuthorizationError):
        await service.get_pipeline_stats(candidate)
