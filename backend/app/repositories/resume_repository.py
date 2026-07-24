"""Resume repository."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.resume import Resume


class ResumeRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, resume: Resume) -> Resume:
        self._db.add(resume)
        await self._db.flush()
        return resume

    async def get_by_id_for_candidate(
        self, resume_id: uuid.UUID, candidate_id: uuid.UUID
    ) -> Resume | None:
        result = await self._db.execute(
            select(Resume).where(Resume.id == resume_id, Resume.candidate_id == candidate_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, resume_id: uuid.UUID) -> Resume | None:
        """Unscoped — used internally once ownership has already been verified elsewhere."""
        return await self._db.get(Resume, resume_id)

    async def list_for_candidate(self, candidate_id: uuid.UUID) -> list[Resume]:
        result = await self._db.execute(
            select(Resume)
            .where(Resume.candidate_id == candidate_id)
            .order_by(Resume.created_at.desc())
        )
        return list(result.scalars().all())
