"""
Email repository.

`get_current_draft` is what makes "clicking Draft again returns the
same in-progress draft instead of creating a duplicate" possible —
CommunicationService checks this before deciding whether to call the
agent at all. See app/models/email.py's DRAFT/SENT lifecycle.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.email import Email, EmailStatus


class EmailRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, email: Email) -> Email:
        self._db.add(email)
        await self._db.flush()
        return email

    async def get_by_id(self, email_id: uuid.UUID) -> Email | None:
        """
        `populate_existing=True` is load-bearing, not decoration: every
        caller of this method (via CommunicationService._reload) calls it
        AFTER mutating and committing this exact row earlier in the same
        session — so the row is already in the session's identity map.
        Plain `session.get()` returns that cached in-memory instance
        without re-querying at all once an object is identity-mapped;
        `updated_at` (an `onupdate=func.now()` column, populated by an
        UPDATE issued without a RETURNING clause) is left in a
        needs-lazy-load state, and Pydantic's synchronous
        `model_validate()` triggering that lazy load outside an awaited
        context is exactly what raises MissingGreenlet. Forcing
        populate_existing makes SQLAlchemy re-issue a real SELECT and
        populate every attribute within this awaited call, so nothing is
        left to lazy-load later. See CommunicationService's module
        docstring for the "re-fetch after every UPDATE" rule this method
        exists to satisfy — this fixes an existing gap in it, not a new
        requirement: the intent was always "return demonstrably fresh
        data," and a same-session identity-mapped get() silently wasn't
        doing that.
        """
        return await self._db.get(Email, email_id, populate_existing=True)

    async def get_by_id_for_company(
        self, email_id: uuid.UUID, company_id: uuid.UUID
    ) -> Email | None:
        result = await self._db.execute(
            select(Email).where(Email.id == email_id, Email.company_id == company_id)
        )
        return result.scalar_one_or_none()

    async def get_current_draft(
        self, application_id: uuid.UUID, email_type: str
    ) -> Email | None:
        result = await self._db.execute(
            select(Email)
            .where(
                Email.application_id == application_id,
                Email.email_type == email_type,
                Email.status == EmailStatus.DRAFT.value,
            )
            .order_by(Email.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def list_for_application(self, application_id: uuid.UUID) -> list[Email]:
        result = await self._db.execute(
            select(Email)
            .where(Email.application_id == application_id)
            .order_by(Email.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_recent_drafts_for_company(
        self, company_id: uuid.UUID, *, limit: int = 10
    ) -> list[Email]:
        """Backs the Dashboard's "pending recruiter actions" section — draft
        emails (of any type) still awaiting recruiter review/send."""
        result = await self._db.execute(
            select(Email)
            .where(Email.company_id == company_id, Email.status == EmailStatus.DRAFT.value)
            .order_by(Email.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
