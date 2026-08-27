"""
Employee repository.

`get_by_application_id` is the idempotency check — EmployeeService
consults this before creating an Employee, so triggering the hire
workflow twice for the same Application returns the existing row
instead of raising a UNIQUE-constraint IntegrityError. Same
"check first, DB constraint is the second layer" discipline as
EmailRepository.get_current_draft.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.employee import Employee


class EmployeeRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, employee: Employee) -> Employee:
        self._db.add(employee)
        await self._db.flush()
        return employee

    async def get_by_id(self, employee_id: uuid.UUID) -> Employee | None:
        return await self._db.get(Employee, employee_id)

    async def get_by_application_id(self, application_id: uuid.UUID) -> Employee | None:
        result = await self._db.execute(
            select(Employee).where(Employee.application_id == application_id)
        )
        return result.scalar_one_or_none()
