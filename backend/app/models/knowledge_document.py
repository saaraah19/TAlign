"""
KnowledgeDocument model.

Owned by a Company — every internal role (not candidates) can query
against a company's knowledge base once uploaded and processed. This is
the "identity" half of the Knowledge Agent's data, same split as
Resume/ParsedResume: a document's metadata and lifecycle live here;
its actual searchable content lives in KnowledgeChunk (many rows per
document), which is what the vector search actually queries.

Pipeline is a real state machine, same two-layer discipline as Job and
Application (DB CHECK constrains valid values only; the transition
GRAPH lives in KnowledgeDocumentService):

    UPLOADED -> TEXT_EXTRACTED -> CHUNKED -> EMBEDDED -> READY
    FAILED is reachable from any non-terminal state.

Split matches Resume Intelligence's existing "deterministic eagerly,
LLM-touching in background" precedent exactly:
  - UPLOADED -> TEXT_EXTRACTED -> CHUNKED happens synchronously in the
    upload request (file I/O + pypdf/docx + chunking — zero network
    calls, all fast).
  - CHUNKED -> EMBEDDED -> READY happens in a background task (the one
    step that calls Google's embedding API).

`embedding_model` / `embedding_dimension` / `embedding_version` are
provenance fields, same spirit as ParsedResume's llm_provider/llm_model/
prompt_version — they exist specifically so that when the embedding
model or chunking strategy changes later, it's possible to query "which
documents were indexed with the old model/version" and decide what
needs re-indexing, rather than guessing. `last_processed_at` is set
only when a document successfully reaches READY — that's the
meaningful "last successfully indexed" timestamp for that purpose.

Reindexing (POST /knowledge/documents/{id}/reindex, admin-only) is
deliberately NOT a graph edge from READY back to UPLOADED — that would
read as the same kind of "going backward" Job's state machine already
disallows for normal flow. It's a distinct admin action
(KnowledgeDocumentService.reindex) that resets this row and re-enters
the forward pipeline fresh, conceptually a reset rather than a
transition.
"""

import uuid
from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.company import Company
    from app.models.user import User


class DocumentCategory(StrEnum):
    POLICY = "policy"
    BENEFITS = "benefits"
    PROCEDURE = "procedure"
    OTHER = "other"


class DocumentStatus(StrEnum):
    UPLOADED = "uploaded"
    TEXT_EXTRACTED = "text_extracted"
    CHUNKED = "chunked"
    EMBEDDED = "embedded"
    READY = "ready"
    FAILED = "failed"


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"
    __table_args__ = (
        CheckConstraint(
            "category IN ('policy', 'benefits', 'procedure', 'other')",
            name="ck_knowledge_documents_category_valid",
        ),
        CheckConstraint(
            "status IN ('uploaded', 'text_extracted', 'chunked', 'embedded', 'ready', 'failed')",
            name="ck_knowledge_documents_status_valid",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(30), nullable=False, default=DocumentCategory.OTHER)

    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)

    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=DocumentStatus.UPLOADED
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # --- Embedding provenance — see module docstring ---
    embedding_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    embedding_dimension: Mapped[int | None] = mapped_column(Integer, nullable=True)
    embedding_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    last_processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    company: Mapped["Company"] = relationship()
    uploader: Mapped["User | None"] = relationship()

    def __repr__(self) -> str:  # pragma: no cover
        return f"<KnowledgeDocument id={self.id} title={self.title!r} status={self.status}>"
