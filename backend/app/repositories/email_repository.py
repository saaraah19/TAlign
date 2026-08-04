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
        return await self._db.get(Email, email_id)

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
