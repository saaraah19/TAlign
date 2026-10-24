"""
KnowledgeChunk repository.

This file contains the one query with no precedent anywhere else in
the codebase — the vector similarity search — so it gets extra care,
per HANDOVER.md's explicit callout.

SECURITY: `search_similar` filters by `company_id` as the FIRST
condition in its WHERE clause, non-negotiable. This is the query that
runs on every single Compass knowledge question; a missing or
incorrectly-ordered filter here is a cross-tenant data leak, not a
cosmetic bug. See tests/test_knowledge_company_scoping.py, which exists
specifically to prove this filter can never be bypassed — this is
deliberately NOT left to "inherited confidence" from the pattern used
by JobRepository/ApplicationRepository elsewhere.

`RetrievalMode` (Amendment 4 in the approved architecture) is a
future-proofing enum, not a real feature yet: HYBRID raises
NotImplementedError rather than silently falling back to VECTOR, so a
caller that requests hybrid retrieval before it's built gets a loud
failure instead of a wrong answer that looks correct.
"""

import uuid
from enum import StrEnum

from sqlalchemy import delete as sa_delete
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.knowledge_chunk import KnowledgeChunk


class RetrievalMode(StrEnum):
    VECTOR = "vector"
    #: Not implemented in this slice — see module docstring. Reserved so
    #: a future keyword/vector hybrid search has a place to plug in
    #: without changing this enum's shape or any caller's signature.
    HYBRID = "hybrid"


class KnowledgeChunkRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create_many(self, chunks: list[KnowledgeChunk]) -> list[KnowledgeChunk]:
        """
        Used at the CHUNKED pipeline stage — chunks are persisted with
        `embedding=NULL` (text already split, no vectors yet); the
        embedding background task fetches them back via
        `list_for_document` and sets `.embedding` on each in place.
        """
        self._db.add_all(chunks)
        await self._db.flush()
        return chunks

    async def list_for_document(self, document_id: uuid.UUID) -> list[KnowledgeChunk]:
        """
        Returns already-tracked ORM instances in chunk order. The
        embedding background task mutates `.embedding` on each returned
        row directly and commits — same "fetch tracked entity, mutate,
        commit" pattern JobService uses for status transitions, no
        separate `update` method needed on this repository.
        """
        result = await self._db.execute(
            select(KnowledgeChunk)
            .where(KnowledgeChunk.document_id == document_id)
            .order_by(KnowledgeChunk.chunk_index)
        )
        return list(result.scalars().all())

    async def delete_for_document(self, document_id: uuid.UUID) -> None:
        """
        Bulk delete, not a per-row `session.delete()` loop like
        JobRepository.delete — reindex can delete dozens of chunk rows
        at once and there's no per-row ORM cascade or event logic on
        KnowledgeChunk that a bulk DELETE would skip, so the loop's
        overhead buys nothing here. Used by the reindex flow (Amendment
        5): delete existing chunks, reset the document to UPLOADED,
        re-enter the pipeline fresh — the document row itself is kept
        (unlike KnowledgeDocumentRepository.delete, which relies on
        DB-level cascade for a full document removal).
        """
        await self._db.execute(sa_delete(KnowledgeChunk).where(KnowledgeChunk.document_id == document_id))
        await self._db.flush()

    async def search_similar(
        self,
        *,
        company_id: uuid.UUID,
        query_embedding: list[float],
        top_k: int,
        mode: RetrievalMode = RetrievalMode.VECTOR,
    ) -> list[tuple[KnowledgeChunk, float]]:
        """
        Returns (chunk, similarity) pairs, ranked highest-similarity
        first. `similarity` is cosine similarity in [-1, 1] (in
        practice ~[0, 1] for normalized embedding models), derived as
        `1 - cosine_distance` — pgvector's `<=>` operator returns
        distance, and KnowledgeQueryService / confidence.py both reason
        in similarity terms, so the conversion happens here once rather
        than being duplicated at every call site.

        Excludes chunks with a NULL embedding (not yet at the EMBEDDED
        pipeline stage) — comparing against a null vector isn't a
        "chunk that just scores low", it's not a candidate at all.

        Eager-loads `KnowledgeChunk.document` via `selectinload` — same
        precedent as ApplicationRepository — so callers (KnowledgeQueryService)
        can read `chunk.document.title` for citations without a lazy-load
        outside an async context (the exact MissingGreenlet bug class this
        codebase already hit once, see HANDOVER.md's Post-Slice-4 fixes).
        """
        if mode is RetrievalMode.HYBRID:
            raise NotImplementedError(
                "RetrievalMode.HYBRID is not implemented yet — see this module's docstring."
            )

        distance = KnowledgeChunk.embedding.cosine_distance(query_embedding)
        similarity = (1 - distance).label("similarity")

        result = await self._db.execute(
            select(KnowledgeChunk, similarity)
            .options(selectinload(KnowledgeChunk.document))
            .where(
                KnowledgeChunk.company_id == company_id,
                KnowledgeChunk.embedding.is_not(None),
            )
            .order_by(distance)
            .limit(top_k)
        )
        return [(row[0], row[1]) for row in result.all()]
