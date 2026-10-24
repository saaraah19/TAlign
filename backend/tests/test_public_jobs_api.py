"""
Tests for the public (candidate-facing) job board.

History worth knowing, because these tests exist to prevent a repeat:
in the Jobs redesign `JobListResponse` was changed to carry
`JobWithStatsRead` items (applicant counts, per-stage counts) for the
recruiter's Jobs page. The public endpoint kept building that same
response from plain `JobRead` objects, so every request to
/api/v1/public/jobs failed validation with a 500 — and the browser
reported it as a CORS error. The service-level tests mock their
repositories and never exercise a route's response model, so nothing
caught it.

Two further contracts are pinned here:
  - the public response never carries internal fields (the recruiter's
    internal user id, the company id, applicant statistics), and does
    carry the employer's name;
  - the repository loads `Job.company` eagerly, because reading an
    unloaded relationship in async SQLAlchemy raises MissingGreenlet.

The route tests drive the real route (real FastAPI app, real response
model) with only the database session and the service call replaced.
"""

import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.sql import Select

from app.core.exceptions import NotFoundError
from app.database.session import get_db
from app.main import app
from app.repositories.job_repository import JobRepository
from app.schemas.job import JobRead, PublicJobListResponse, PublicJobRead
from app.services.job_service import JobService

# Everything that must never appear in a public job.
INTERNAL_FIELDS = {
    "applicant_count",
    "stage_counts",  # recruiter-only pipeline statistics
    "company_id",
    "created_by",  # internal ids
    "status",
    "updated_at",  # not meaningful to a visitor
}


def _fake_orm_job(title: str, status: str = "open") -> SimpleNamespace:
    """
    Looks like a Job row to `from_attributes` validation — no database
    involved. It deliberately DOES carry the internal attributes
    (company_id, created_by, status): the point is that the public schema
    leaves them out even when the source object has them.
    """
    now = datetime(2026, 10, 9, tzinfo=UTC)
    return SimpleNamespace(
        id=uuid.uuid4(),
        company_id=uuid.uuid4(),
        created_by=uuid.uuid4(),
        company=SimpleNamespace(name="Acme Corp"),
        title=title,
        description="Build and run our backend services.",
        employment_type="full_time",
        location="Remote",
        salary_min=None,
        salary_max=None,
        salary_currency="USD",
        status=status,
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

    async def fake_get_open_job(self: JobService, *, job_id: uuid.UUID) -> Any:
        if job_id == uuid.UUID(int=0):
            raise NotFoundError("Job not found.")
        return _fake_orm_job("Backend Engineer")

    app.dependency_overrides[get_db] = fake_db
    monkeypatch.setattr(JobService, "list_open_jobs", fake_list_open_jobs)
    monkeypatch.setattr(JobService, "get_open_job", fake_get_open_job)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            yield c
    finally:
        app.dependency_overrides.pop(get_db, None)


# --- the list endpoint ---------------------------------------------------


async def test_public_job_list_returns_200_with_jobs(client: AsyncClient) -> None:
    response = await client.get("/api/v1/public/jobs")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert [item["title"] for item in body["items"]] == ["Backend Engineer", "Designer"]


async def test_public_job_list_shows_the_employer_name(client: AsyncClient) -> None:
    body = (await client.get("/api/v1/public/jobs")).json()

    assert all(item["company_name"] == "Acme Corp" for item in body["items"])


async def test_public_job_list_never_exposes_internal_fields(client: AsyncClient) -> None:
    body = (await client.get("/api/v1/public/jobs")).json()

    for item in body["items"]:
        leaked = INTERNAL_FIELDS & set(item)
        assert not leaked, f"internal fields leaked to the public: {leaked}"


# --- the single-job endpoint --------------------------------------------


async def test_public_job_detail_returns_the_job_with_employer_name(client: AsyncClient) -> None:
    response = await client.get(f"/api/v1/public/jobs/{uuid.uuid4()}")

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Backend Engineer"
    assert body["company_name"] == "Acme Corp"
    assert not (INTERNAL_FIELDS & set(body))


async def test_public_job_detail_returns_404_for_an_unavailable_job(client: AsyncClient) -> None:
    response = await client.get(f"/api/v1/public/jobs/{uuid.UUID(int=0)}")

    assert response.status_code == 404


# --- structure: a field that isn't declared can't leak -------------------


def test_public_schemas_are_structurally_free_of_internal_fields() -> None:
    assert not (INTERNAL_FIELDS & set(PublicJobRead.model_fields))
    assert PublicJobListResponse.model_fields["items"].annotation == list[PublicJobRead]


def test_the_staff_schema_is_unchanged_so_recruiters_keep_what_they_had() -> None:
    # The public view is a separate type; the staff view must keep these.
    assert {"company_id", "created_by", "status"} <= set(JobRead.model_fields)


# --- the async trap: the company must be loaded eagerly ------------------


def _eagerly_loads_company(statement: Select[Any]) -> bool:
    """True if the statement carries a loader option for Job.company that loads it in the query."""
    for option in statement._with_options:
        for element in option.context:
            if "Job.company" in str(element.path) and element.strategy[0][1] in (
                "selectin",
                "joined",
            ):
                return True
    return False


def _db_capturing_statements(statements: list[Select[Any]]) -> AsyncMock:
    class _Result:
        def scalar_one(self) -> int:
            return 0

        def scalar_one_or_none(self) -> None:
            return None

        def scalars(self) -> SimpleNamespace:
            return SimpleNamespace(all=list)

    async def execute(statement: Select[Any]) -> _Result:
        statements.append(statement)
        return _Result()

    db = AsyncMock()
    db.execute = execute
    return db


async def test_list_open_loads_the_company_eagerly() -> None:
    statements: list[Select[Any]] = []
    await JobRepository(_db_capturing_statements(statements)).list_open()

    assert any(_eagerly_loads_company(s) for s in statements), (
        "list_open must eager-load Job.company: the public response reads "
        "job.company.name and a lazy load raises MissingGreenlet in async code"
    )


async def test_get_open_with_company_loads_the_company_eagerly() -> None:
    statements: list[Select[Any]] = []
    await JobRepository(_db_capturing_statements(statements)).get_open_with_company(uuid.uuid4())

    assert statements
    assert all(_eagerly_loads_company(s) for s in statements)


# --- the service rule: only OPEN jobs are public ------------------------


async def test_service_hides_jobs_that_are_not_open() -> None:
    repository = AsyncMock()
    repository.get_open_with_company.return_value = _fake_orm_job("Secret", status="draft")

    with pytest.raises(NotFoundError):
        await JobService(AsyncMock(), job_repository=repository).get_open_job(job_id=uuid.uuid4())


async def test_service_returns_an_open_job() -> None:
    repository = AsyncMock()
    open_job = _fake_orm_job("Visible", status="open")
    repository.get_open_with_company.return_value = open_job

    job = await JobService(AsyncMock(), job_repository=repository).get_open_job(job_id=uuid.uuid4())

    assert job is open_job


async def test_service_treats_a_missing_job_as_not_found() -> None:
    repository = AsyncMock()
    repository.get_open_with_company.return_value = None

    with pytest.raises(NotFoundError):
        await JobService(AsyncMock(), job_repository=repository).get_open_job(job_id=uuid.uuid4())
