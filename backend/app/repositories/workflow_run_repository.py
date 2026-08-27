"""
WorkflowRun repository.

Write-once — there is deliberately no `update` method. Every call site
creates exactly one row per trigger attempt (SUCCESS, FAILED, or
SKIPPED — see app/models/workflow_run.py) and never revises it.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workflow_run import WorkflowRun


class WorkflowRunRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, run: WorkflowRun) -> WorkflowRun:
        self._db.add(run)
        await self._db.flush()
        return run

    async def list_for_company(
        self, company_id: uuid.UUID, *, limit: int = 50
    ) -> list[WorkflowRun]:
        result = await self._db.execute(
            select(WorkflowRun)
            .where(WorkflowRun.company_id == company_id)
            .order_by(WorkflowRun.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_latest_for_trigger(
        self, trigger_entity_type: str, trigger_entity_id: uuid.UUID
    ) -> WorkflowRun | None:
        """Used by the recruiter-facing hire-workflow status read (see
        app/workflow_engine/status.py) to show the most recent run's
        outcome for a given Application."""
        result = await self._db.execute(
            select(WorkflowRun)
            .where(
                WorkflowRun.trigger_entity_type == trigger_entity_type,
                WorkflowRun.trigger_entity_id == trigger_entity_id,
            )
            .order_by(WorkflowRun.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
