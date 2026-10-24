"""
Company repository.

Pure data access — no business rules here (e.g. it does NOT decide
whether a slug is "acceptable," it just checks existence). Rule
enforcement belongs to AuthService, per the layering CLAUDE.md and the
new Compass-scope rule both establish: repositories ↔ data, services ↔
business logic.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Company


class CompanyRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, company: Company) -> Company:
        self._db.add(company)
        await self._db.flush()
        return company

    async def get_by_id(self, company_id: uuid.UUID) -> Company | None:
        return await self._db.get(Company, company_id)

    async def get_by_slug(self, slug: str) -> Company | None:
        result = await self._db.execute(select(Company).where(Company.slug == slug))
        return result.scalar_one_or_none()

    async def slug_exists(self, slug: str) -> bool:
        return await self.get_by_slug(slug) is not None
