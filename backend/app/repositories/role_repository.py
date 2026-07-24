"""
Role repository.

Roles are seed data (inserted by the Slice 1 migration, one row per
`app.core.roles.Role` value) — this repository only ever reads them.
Nothing in the application layer creates or deletes Role rows.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.roles import Role as RoleEnum
from app.models.role import Role


class RoleRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_by_name(self, name: RoleEnum) -> Role | None:
        result = await self._db.execute(select(Role).where(Role.name == name.value))
        return result.scalar_one_or_none()
