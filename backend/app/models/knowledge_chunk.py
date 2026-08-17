"""
KnowledgeChunk model.

The table retrieval actually queries. One document produces many
chunks (see app/utils/knowledge_chunking.py for how text is split);
each chunk carries its own embedding vector.

`company_id` is denormalized here even though it's derivable via
`document_id -> KnowledgeDocument.company_id` — same pattern as
Application/Email, but load-bearing in a way it isn't always
elsewhere: the retrieval query is `WHERE company_id = :company_id
ORDER BY embedding <=> :query_vector LIMIT k`, and having company_id
directly on the table being vector-searched (rather than requiring a
join through KnowledgeDocument on every query) keeps the tenant-
isolation filter as cheap and direct as possible — this is the query
that runs on every single Compass knowledge question, so it's worth
being deliberate about.

`embedding` is nullable at the DB level even though a document that has
reached DocumentStatus.READY should never have a null embedding on any
of its chunks — chunks are inserted at the CHUNKED pipeline stage
(text already split, no vectors yet) and updated in place once the
EMBEDDED stage completes. Same "column is nullable because of a real
intermediate state, not because the data is optional" reasoning used
elsewhere in this codebase (e.g. Resume.raw_text).

Fixed at 768 dimensions — see docs/06_slice6_knowledge_agent.md for
the embedding model decision (gemini-embedding-001, truncated via
Matryoshka Representation Learning from its native 3072 dimensions).
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, ForeignKey, Index, Integer, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.knowledge_document import KnowledgeDocument

EMBEDDING_DIMENSION = 768


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"
    __table_args__ = (
        # Company-scoped composite index — every retrieval query filters
        # by company_id first; no ANN (ivfflat/hnsw) index yet, see the
        # architecture doc's reasoning on why one isn't justified at
        # MVP data volumes.
        Index("ix_knowledge_chunks_company_document", "company_id", "document_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("knowledge_documents.id", ondelete="CASCADE"), nullable=False
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )

    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(EMBEDDING_DIMENSION), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    document: Mapped["KnowledgeDocument"] = relationship()

    def __repr__(self) -> str:  # pragma: no cover
        return f"<KnowledgeChunk id={self.id} document_id={self.document_id} index={self.chunk_index}>"
