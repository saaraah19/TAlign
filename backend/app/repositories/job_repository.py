"""
Job repository.

Every method that touches a specific job takes `company_id` and filters
on it in the query itself (not as an after-the-fetch check) — this is
what makes cross-company access return "not found" at the data layer
rather than relying on a service-layer `if` a future refactor could
accidentally drop.
"""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application import Application
from app.models.job import Job, JobStatus


class JobRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, job: Job) -> Job:
        self._db.add(job)
        await self._db.flush()
        return job

    async def get_by_id_for_company(self, job_id: uuid.UUID, company_id: uuid.UUID) -> Job | None:
        result = await self._db.execute(
            select(Job).where(Job.id == job_id, Job.company_id == company_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, job_id: uuid.UUID) -> Job | None:
        """
        Unscoped lookup — no company filter. Used by ApplicationService,
        which isn't acting on behalf of any single company (a candidate
        applying isn't a member of one), and by the public job-browsing
        endpoints. Every OTHER caller should prefer
        `get_by_id_for_company` — this method makes cross-company access
        possible by design, so it's used narrowly and deliberately.
        """
        return await self._db.get(Job, job_id)

    async def list_open(self, *, page: int = 1, page_size: int = 20) -> tuple[list[Job], int]:
        """Public job browsing — every company's OPEN jobs, no auth, no company scoping."""
        base_query = select(Job).where(Job.status == JobStatus.OPEN.value)
        count_query = (
            select(func.count()).select_from(Job).where(Job.status == JobStatus.OPEN.value)
        )
        total = (await self._db.execute(count_query)).scalar_one()
        result = await self._db.execute(
            base_query.order_by(Job.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result.scalars().all()), total

    async def list_for_company(
        self,
        company_id: uuid.UUID,
        *,
        status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Job], int]:
        base_query = select(Job).where(Job.company_id == company_id)
        count_query = select(func.count()).select_from(Job).where(Job.company_id == company_id)

        if status is not None:
            base_query = base_query.where(Job.status == status)
            count_query = count_query.where(Job.status == status)

        total = (await self._db.execute(count_query)).scalar_one()

        result = await self._db.execute(
            base_query.order_by(Job.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result.scalars().all()), total

    async def delete(self, job: Job) -> None:
        await self._db.delete(job)
        await self._db.flush()

    async def list_low_applicant_open_jobs(
        self, company_id: uuid.UUID, *, threshold: int, limit: int = 10
    ) -> list[tuple[Job, int]]:
        """
        Open jobs for this company with fewer than `threshold`
        applications, ordered by applicant count ascending (the ones
        needing the most attention first) — backs the Dashboard's
        "jobs with low applicant volume" section. A LEFT JOIN (not
        INNER) is load-bearing: a job with zero applications must still
        appear, which an INNER JOIN would silently drop.
        """
        applicant_count = func.count(Application.id).label("applicant_count")
        query = (
            select(Job, applicant_count)
            .outerjoin(Application, Application.job_id == Job.id)
            .where(Job.company_id == company_id, Job.status == JobStatus.OPEN.value)
            .group_by(Job.id)
            .having(applicant_count < threshold)
            .order_by(applicant_count.asc())
            .limit(limit)
        )
        result = await self._db.execute(query)
        return [(job, count) for job, count in result.all()]
