"""
Application repository.

Two families of read methods, mirroring who's asking:
  - `*_for_candidate`: scoped to one candidate's own applications
    (candidate dashboard).
  - `*_for_company`: scoped to one company's applications, across all
    its jobs (recruiter pipeline view).

Each eager-loads the relationship its consumer actually needs — the
candidate view needs `job` (title, company name) but not `candidate`
(it's their own); the company view needs `candidate` (name, email) and
`job` (title) but obviously not scoping by candidate.
"""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.application import Application, ApplicationStatus


class ApplicationRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, application: Application) -> Application:
        self._db.add(application)
        await self._db.flush()
        return application

    async def exists_for_candidate_and_job(
        self, candidate_id: uuid.UUID, job_id: uuid.UUID
    ) -> bool:
        result = await self._db.execute(
            select(Application.id).where(
                Application.candidate_id == candidate_id, Application.job_id == job_id
            )
        )
        return result.scalar_one_or_none() is not None

    async def get_by_id(self, application_id: uuid.UUID) -> Application | None:
        """
        Unscoped — no candidate or company filter. Used by the resume
        analysis background task, which runs outside any request/user
        context (see resume_analysis_service.py's
        run_resume_analysis_task) and by ApplicationService's own
        attach_resume, which re-validates ownership itself before
        calling this. Every request-driven read should prefer
        get_by_id_for_candidate / get_by_id_for_company instead.
        """
        return await self._db.get(Application, application_id)

    async def list_awaiting_review_for_company(
        self, company_id: uuid.UUID, *, limit: int = 10
    ) -> list[Application]:
        """
        Backs the Dashboard's "applications awaiting review" section —
        APPLIED or SCREENING, the two statuses that mean "sitting in the
        recruiter's queue, not yet acted on." A dedicated single query
        (status IN (...)) rather than calling list_for_company twice
        (once per status) — simpler and one round-trip instead of two.
        """
        result = await self._db.execute(
            select(Application)
            .options(selectinload(Application.job), selectinload(Application.candidate))
            .where(
                Application.company_id == company_id,
                Application.status.in_(
                    [ApplicationStatus.APPLIED.value, ApplicationStatus.SCREENING.value]
                ),
            )
            .order_by(Application.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_id_with_relations(self, application_id: uuid.UUID) -> Application | None:
        """
        Unscoped, like get_by_id above (same "runs outside any request/
        user context" reasoning) but eager-loads `job` and `candidate` —
        used by the hire workflow's background task
        (app/workflow_engine/tasks.py), which needs the candidate's name/
        email and the job title without a company_id to scope through
        the way get_by_id_for_company has.
        """
        result = await self._db.execute(
            select(Application)
            .options(selectinload(Application.job), selectinload(Application.candidate))
            .where(Application.id == application_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id_for_candidate(
        self, application_id: uuid.UUID, candidate_id: uuid.UUID
    ) -> Application | None:
        result = await self._db.execute(
            select(Application)
            .options(selectinload(Application.job))
            .where(Application.id == application_id, Application.candidate_id == candidate_id)
        )
        return result.scalar_one_or_none()

    async def list_for_candidate(
        self, candidate_id: uuid.UUID, *, page: int = 1, page_size: int = 20
    ) -> tuple[list[Application], int]:
        base_query = (
            select(Application)
            .options(selectinload(Application.job))
            .where(Application.candidate_id == candidate_id)
        )
        count_query = (
            select(func.count())
            .select_from(Application)
            .where(Application.candidate_id == candidate_id)
        )
        total = (await self._db.execute(count_query)).scalar_one()
        result = await self._db.execute(
            base_query.order_by(Application.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result.scalars().all()), total

    async def get_by_id_for_company(
        self, application_id: uuid.UUID, company_id: uuid.UUID
    ) -> Application | None:
        result = await self._db.execute(
            select(Application)
            .options(selectinload(Application.job), selectinload(Application.candidate))
            .where(Application.id == application_id, Application.company_id == company_id)
        )
        return result.scalar_one_or_none()

    async def list_for_company(
        self,
        company_id: uuid.UUID,
        *,
        job_id: uuid.UUID | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Application], int]:
        base_query = (
            select(Application)
            .options(selectinload(Application.job), selectinload(Application.candidate))
            .where(Application.company_id == company_id)
        )
        count_query = (
            select(func.count())
            .select_from(Application)
            .where(Application.company_id == company_id)
        )

        if job_id is not None:
            base_query = base_query.where(Application.job_id == job_id)
            count_query = count_query.where(Application.job_id == job_id)
        if status is not None:
            base_query = base_query.where(Application.status == status)
            count_query = count_query.where(Application.status == status)

        total = (await self._db.execute(count_query)).scalar_one()
        result = await self._db.execute(
            base_query.order_by(Application.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result.scalars().all()), total
