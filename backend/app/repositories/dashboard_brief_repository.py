"""
DashboardBrief repository.

`get_for_company_and_date` is the cache-hit check — DashboardService
consults this before ever calling the LLM. `create` inserts a fresh
brief; the (company_id, brief_date) UNIQUE constraint is the DB-layer
half of "at most one brief per company per day" (service-layer half is
the get-before-create check itself), same two-layer discipline as
every cached/idempotent write elsewhere in this codebase.
"""

import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dashboard_brief import DashboardBrief


class DashboardBriefRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_for_company_and_date(
        self, company_id: uuid.UUID, brief_date: date
    ) -> DashboardBrief | None:
        result = await self._db.execute(
            select(DashboardBrief).where(
                DashboardBrief.company_id == company_id,
                DashboardBrief.brief_date == brief_date,
            )
        )
        return result.scalar_one_or_none()

    async def create(self, brief: DashboardBrief) -> DashboardBrief:
        self._db.add(brief)
        await self._db.flush()
        return brief
