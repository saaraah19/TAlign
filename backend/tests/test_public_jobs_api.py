"""
Regression tests for the public (candidate-facing) job listing.

Why this file exists: in the Jobs redesign, `JobListResponse` was
changed to carry `JobWithStatsRead` items (applicant counts, per-stage
counts) for the recruiter's Jobs page. The public endpoint kept
building that same response from plain `JobRead` objects, so every
request to /api/v1/public/jobs failed validation with a 500 — and the
browser reported it as a CORS error, because an unhandled 500 never
passes through the CORS middleware. The service-level tests mock their
repositories and never exercise this route, so nothing caught it.

These tests drive the real route (real FastAPI app, real response
model) with only the database session and the service call replaced.
"""

import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

from app.database.session import get_db
from app.main import app
from app.schemas.job import JobRead, PublicJobListResponse
from app.services.job_service import JobService

INTERNAL_ONLY_FIELDS = {"applicant_count", "stage_counts"}


def _fake_orm_job(title: str) -> SimpleNamespace:
    """Looks like a Job row to `from_attributes` validation — no database involved."""
    now = datetime(2026, 10, 9, tzinfo=UTC)
    return SimpleNamespace(
        id=uuid.uuid4(),
        company_id=uuid.uuid4(),
        created_by=uuid.uuid4(),
        title=title,
        description="Build and run our backend services.",
        employment_type="full_time",
        location="Remote",
        salary_min=None,
        salary_max=None,
        salary_currency="USD",
        status="open",
        required_skills=["Python"],
        preferred_skills=[],
        min_years_experience=2,
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
async def client(monkeypatch: pytest.MonkeyPatch) -> AsyncIterator[AsyncClient]:
    async def fake_db() -> AsyncIterator[None]:
        yield None

    async def fake_list_open_jobs(
        self: JobService, *, page: int, page_size: int
    ) -> tuple[list[Any], int]:
        return [_fake_orm_job("Backend Engineer"), _fake_orm_job("Designer")], 2

    app.dependency_overrides[get_db] = fake_db
    monkeypatch.setattr(JobService, "list_open_jobs", fake_list_open_jobs)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            yield c
    finally:
        app.dependency_overrides.pop(get_db, None)


async def test_public_job_list_returns_200_with_jobs(client: AsyncClient) -> None:
    response = await client.get("/api/v1/public/jobs")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert [item["title"] for item in body["items"]] == ["Backend Engineer", "Designer"]


async def test_public_job_list_never_exposes_internal_pipeline_stats(
    client: AsyncClient,
) -> None:
    body = (await client.get("/api/v1/public/jobs")).json()

    for item in body["items"]:
        assert INTERNAL_ONLY_FIELDS.isdisjoint(item), (
            "applicant counts and stage counts are recruiter-only data "
            "and must never reach the public endpoint"
        )


def test_public_list_schema_is_structurally_free_of_internal_fields() -> None:
    # Same convention as the candidate-facing analysis schemas: a field
    # that is not in the schema cannot leak, whatever a future caller does.
    assert PublicJobListResponse.model_fields["items"].annotation == list[JobRead]
    assert INTERNAL_ONLY_FIELDS.isdisjoint(JobRead.model_fields)
