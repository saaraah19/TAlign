"""
Tests for the Dashboard KPI computation added alongside the app
redesign: open_jobs_count, active_candidates_count, pending_actions_count,
and stage_counts. The five pre-existing deterministic lists (awaiting
review, low-applicant jobs, recent analyses, recent workflow runs,
pending drafts) already have no dedicated test file (a pre-existing gap,
not introduced here) -- this file covers only the new aggregation logic,
with the Daily Brief short-circuited via an existing cached row so the
LLM agent is never invoked.
"""

import uuid
from datetime import date
from unittest.mock import AsyncMock

from app.models.application import ApplicationStatus
from app.models.dashboard_brief import DashboardBrief
from app.models.user import User
from app.services.dashboard_service import DashboardService


def _make_service(
    *,
    status_counts: dict[str, int],
    open_jobs: int,
    awaiting_review_count: int = 0,
    pending_drafts_count: int = 0,
):
    application_repo = AsyncMock()
    application_repo.list_awaiting_review_for_company.return_value = [
        object() for _ in range(awaiting_review_count)
    ]
    application_repo.count_by_status_for_company.return_value = status_counts

    job_repo = AsyncMock()
    job_repo.list_low_applicant_open_jobs.return_value = []
    job_repo.count_open.return_value = open_jobs

    email_repo = AsyncMock()
    email_repo.list_recent_drafts_for_company.return_value = [
        object() for _ in range(pending_drafts_count)
    ]

    resume_analysis_repo = AsyncMock()
    resume_analysis_repo.list_recent_completed_for_company.return_value = []

    workflow_run_repo = AsyncMock()
    workflow_run_repo.list_for_company.return_value = []

    # Short-circuit brief generation via an already-cached row for today
    # -- this test suite is about KPI math, not the LLM briefing.
    brief_repo = AsyncMock()
    brief_repo.get_for_company_and_date.return_value = DashboardBrief(
        id=uuid.uuid4(),
        company_id=uuid.uuid4(),
        brief_date=date(2026, 6, 1),
        summary="cached",
        recommended_actions=[],
        llm_provider="fake",
        llm_model="fake",
        prompt_version="v1",
    )

    db = AsyncMock()
    service = DashboardService(
        db,
        application_repository=application_repo,
        job_repository=job_repo,
        email_repository=email_repo,
        resume_analysis_repository=resume_analysis_repo,
        workflow_run_repository=workflow_run_repo,
        dashboard_brief_repository=brief_repo,
    )
    return service


def _acting_user(company_id: uuid.UUID | None = None) -> User:
    return User(
        id=uuid.uuid4(),
        company_id=company_id or uuid.uuid4(),
        account_type="internal",
        email="sarah@example.com",
        password_hash="x",
        first_name="Sarah",
        last_name="Lopez",
    )


async def test_stage_counts_fills_zero_for_missing_statuses() -> None:
    service = _make_service(status_counts={"applied": 3, "hired": 1}, open_jobs=2)

    data = await service.get_dashboard(_acting_user())

    assert data.stage_counts == {
        "applied": 3,
        "screening": 0,
        "interview": 0,
        "offer": 0,
        "hired": 1,
        "rejected": 0,
    }


async def test_active_candidates_excludes_hired_and_rejected() -> None:
    service = _make_service(
        status_counts={
            "applied": 5,
            "screening": 2,
            "interview": 1,
            "offer": 1,
            "hired": 10,
            "rejected": 7,
        },
        open_jobs=1,
    )

    data = await service.get_dashboard(_acting_user())

    assert data.active_candidates_count == 5 + 2 + 1 + 1
    assert data.active_candidates_count != sum(
        [5, 2, 1, 1, 10, 7]
    )  # sanity: hired/rejected genuinely excluded


async def test_open_jobs_count_comes_from_the_job_repository() -> None:
    service = _make_service(status_counts={}, open_jobs=4)

    data = await service.get_dashboard(_acting_user())

    assert data.open_jobs_count == 4


async def test_pending_actions_sums_awaiting_review_and_pending_drafts() -> None:
    service = _make_service(
        status_counts={}, open_jobs=0, awaiting_review_count=3, pending_drafts_count=2
    )

    data = await service.get_dashboard(_acting_user())

    assert data.pending_actions_count == 5


async def test_stage_counts_always_has_all_six_statuses_even_when_empty() -> None:
    service = _make_service(status_counts={}, open_jobs=0)

    data = await service.get_dashboard(_acting_user())

    assert set(data.stage_counts.keys()) == {s.value for s in ApplicationStatus}
    assert all(count == 0 for count in data.stage_counts.values())
