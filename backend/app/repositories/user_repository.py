"""
User repository.

Every read method eager-loads `role_links.role` via `selectinload` —
callers (services, auth dependencies) always need roles alongside the
user, and this avoids N+1 queries or, worse, lazy-load errors on an
already-closed async session.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.role import UserRole
from app.models.user import User


class UserRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    def _base_query(self):
        return select(User).options(selectinload(User.role_links).selectinload(UserRole.role))

    async def create(self, user: User) -> User:
        self._db.add(user)
        await self._db.flush()
        return user

    async def add_role(self, user_id: uuid.UUID, role_id: uuid.UUID) -> None:
        self._db.add(UserRole(user_id=user_id, role_id=role_id))
        await self._db.flush()

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        result = await self._db.execute(self._base_query().where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        result = await self._db.execute(self._base_query().where(User.email == email.lower()))
        return result.scalar_one_or_none()

    async def email_exists(self, email: str) -> bool:
        return await self.get_by_email(email) is not None
