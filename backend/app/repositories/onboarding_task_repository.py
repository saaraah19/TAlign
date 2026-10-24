"""
OnboardingTask repository.

`exists_for_employee` backs the second half of the hire workflow's
idempotency guard: even though `Employee.application_id` being UNIQUE
already prevents a second Employee row, checking here too means the
onboarding-checklist step never doubles up even if it were ever called
in isolation (e.g. a future retry of just that step).
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.onboarding_task import OnboardingTask


class OnboardingTaskRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create_many(self, tasks: list[OnboardingTask]) -> list[OnboardingTask]:
        self._db.add_all(tasks)
        await self._db.flush()
        return tasks

    async def list_for_employee(self, employee_id: uuid.UUID) -> list[OnboardingTask]:
        result = await self._db.execute(
            select(OnboardingTask)
            .where(OnboardingTask.employee_id == employee_id)
            .order_by(OnboardingTask.created_at)
        )
        return list(result.scalars().all())

    async def exists_for_employee(self, employee_id: uuid.UUID) -> bool:
        result = await self._db.execute(
            select(OnboardingTask.id).where(OnboardingTask.employee_id == employee_id).limit(1)
        )
        return result.scalar_one_or_none() is not None
