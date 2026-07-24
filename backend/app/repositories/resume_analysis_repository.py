"""
ResumeAnalysis repository.

Every write is an INSERT — there is no `update` method here at all,
deliberately. Re-analysis (ResumeAnalysisService) always calls `create`,
never fetches-then-mutates an existing row. That's what "never overwrite
a historical analysis" means as an enforced fact rather than a
convention someone could accidentally violate.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application import Application
from app.models.resume_analysis import AnalysisStatus, ResumeAnalysis


class ResumeAnalysisRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, analysis: ResumeAnalysis) -> ResumeAnalysis:
        self._db.add(analysis)
        await self._db.flush()
        return analysis

    async def get_by_id(self, analysis_id: uuid.UUID) -> ResumeAnalysis | None:
        return await self._db.get(ResumeAnalysis, analysis_id)

    async def get_latest_for_application(
        self, application_id: uuid.UUID
    ) -> ResumeAnalysis | None:
        """Latest row regardless of status — callers decide how to handle pending/failed."""
        result = await self._db.execute(
            select(ResumeAnalysis)
            .where(ResumeAnalysis.application_id == application_id)
            .order_by(ResumeAnalysis.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_latest_completed_for_application(
        self, application_id: uuid.UUID
    ) -> ResumeAnalysis | None:
        result = await self._db.execute(
            select(ResumeAnalysis)
            .where(
                ResumeAnalysis.application_id == application_id,
                ResumeAnalysis.status == AnalysisStatus.COMPLETED.value,
            )
            .order_by(ResumeAnalysis.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def list_history_for_application(
        self, application_id: uuid.UUID
    ) -> list[ResumeAnalysis]:
        """Every version, newest first — internal HR use only (see ApplicationService RBAC)."""
        result = await self._db.execute(
            select(ResumeAnalysis)
            .where(ResumeAnalysis.application_id == application_id)
            .order_by(ResumeAnalysis.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_id_for_company(
        self, analysis_id: uuid.UUID, company_id: uuid.UUID
    ) -> ResumeAnalysis | None:
        """Company-scoped via a join through Application — mirrors the Slice 2-3 scoping pattern."""
        result = await self._db.execute(
            select(ResumeAnalysis)
            .join(Application, Application.id == ResumeAnalysis.application_id)
            .where(ResumeAnalysis.id == analysis_id, Application.company_id == company_id)
        )
        return result.scalar_one_or_none()
