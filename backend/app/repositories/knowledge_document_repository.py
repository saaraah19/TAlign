"""
KnowledgeDocument repository.

Every method that scopes to a specific document takes `company_id` and
filters on it in the query itself — same discipline as JobRepository:
cross-company access returns "not found" at the data layer, not via a
service-layer check a future refactor could accidentally drop.
"""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge_document import KnowledgeDocument


class KnowledgeDocumentRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, document: KnowledgeDocument) -> KnowledgeDocument:
        self._db.add(document)
        await self._db.flush()
        return document

    async def get_by_id_for_company(
        self, document_id: uuid.UUID, company_id: uuid.UUID
    ) -> KnowledgeDocument | None:
        result = await self._db.execute(
            select(KnowledgeDocument).where(
                KnowledgeDocument.id == document_id,
                KnowledgeDocument.company_id == company_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, document_id: uuid.UUID) -> KnowledgeDocument | None:
        """
        Unscoped lookup — no company filter. Used by the embedding
        background task (KnowledgeDocumentService's CHUNKED -> EMBEDDED
        -> READY step), which runs outside any request/user context —
        same precedent as ApplicationRepository.get_by_id and
        JobRepository.get_by_id. Every request-driven read should
        prefer get_by_id_for_company instead.
        """
        return await self._db.get(KnowledgeDocument, document_id)

    async def list_for_company(
        self,
        company_id: uuid.UUID,
        *,
        category: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[KnowledgeDocument], int]:
        base_query = select(KnowledgeDocument).where(KnowledgeDocument.company_id == company_id)
        count_query = (
            select(func.count())
            .select_from(KnowledgeDocument)
            .where(KnowledgeDocument.company_id == company_id)
        )

        if category is not None:
            base_query = base_query.where(KnowledgeDocument.category == category)
            count_query = count_query.where(KnowledgeDocument.category == category)

        total = (await self._db.execute(count_query)).scalar_one()
        result = await self._db.execute(
            base_query.order_by(KnowledgeDocument.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result.scalars().all()), total

    async def delete(self, document: KnowledgeDocument) -> None:
        """
        Deletes the document row. Its chunks cascade-delete at the DB
        level (KnowledgeChunk.document_id has ondelete="CASCADE" — see
        that model) so callers do NOT need to delete chunks separately
        for a full document deletion. Reindex is different — it keeps
        the document row and explicitly deletes only its chunks via
        KnowledgeChunkRepository.delete_for_document.
        """
        await self._db.delete(document)
        await self._db.flush()
