"""
ParsedResume repository.

`get_latest_completed_for_resume` is what makes extraction reuse
possible — ResumeAnalysisService calls this before deciding whether a
fresh LLM extraction call is even necessary. See app/models/parsed_resume.py
for the full reasoning.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.parsed_resume import ParsedResume, ParsedResumeStatus


class ParsedResumeRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, parsed_resume: ParsedResume) -> ParsedResume:
        self._db.add(parsed_resume)
        await self._db.flush()
        return parsed_resume

    async def get_latest_completed_for_resume(self, resume_id: uuid.UUID) -> ParsedResume | None:
        result = await self._db.execute(
            select(ParsedResume)
            .where(
                ParsedResume.resume_id == resume_id,
                ParsedResume.status == ParsedResumeStatus.COMPLETED.value,
            )
            .order_by(ParsedResume.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_latest_for_resume(self, resume_id: uuid.UUID) -> ParsedResume | None:
        """Latest row regardless of status — used to look up a just-failed attempt's id."""
        result = await self._db.execute(
            select(ParsedResume)
            .where(ParsedResume.resume_id == resume_id)
            .order_by(ParsedResume.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, parsed_resume_id: uuid.UUID) -> ParsedResume | None:
        return await self._db.get(ParsedResume, parsed_resume_id)
