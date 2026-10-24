"""slice6_knowledge_agent

Revision ID: d3e4f5a6b7c8
Revises: c2d3e4f5a6b7
Create Date: 2026-07-28

Slice 6: Knowledge Agent (RAG).

Enables the pgvector extension (already provisioned in the Postgres
image since Slice 0 — docker-compose.yml uses `pgvector/pgvector:pg16`
— but never actually turned on until now, since nothing used embeddings
before this slice) and creates the two Knowledge tables. See
app/models/knowledge_document.py and app/models/knowledge_chunk.py for
the full reasoning behind the explicit pipeline states and the
embedding provenance fields.
"""

from collections.abc import Sequence

import pgvector.sqlalchemy
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "d3e4f5a6b7c8"
down_revision: str | None = "c2d3e4f5a6b7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "knowledge_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("uploaded_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=30), nullable=False, server_default="other"),
        sa.Column("file_path", sa.String(length=1024), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=100), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="uploaded"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("embedding_model", sa.String(length=100), nullable=True),
        sa.Column("embedding_dimension", sa.Integer(), nullable=True),
        sa.Column("embedding_version", sa.String(length=50), nullable=True),
        sa.Column("last_processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["uploaded_by"], ["users.id"], ondelete="SET NULL"),
        sa.CheckConstraint(
            "category IN ('policy', 'benefits', 'procedure', 'other')",
            name="ck_knowledge_documents_category_valid",
        ),
        sa.CheckConstraint(
            "status IN ('uploaded', 'text_extracted', 'chunked', 'embedded', 'ready', 'failed')",
            name="ck_knowledge_documents_status_valid",
        ),
    )
    op.create_index(
        "ix_knowledge_documents_company_id", "knowledge_documents", ["company_id"]
    )
    op.create_index(
        "ix_knowledge_documents_company_status",
        "knowledge_documents",
        ["company_id", "status"],
    )

    op.create_table(
        "knowledge_chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=False),
        sa.Column("embedding", pgvector.sqlalchemy.Vector(768), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["document_id"], ["knowledge_documents.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
    )
    # Composite, company-first — every retrieval query filters by
    # company_id before anything else. No ANN (ivfflat/hnsw) index yet;
    # see docs/06_slice6_knowledge_agent.md for why one isn't justified
    # at MVP data volumes — a plain index + seq scan is faster than a
    # poorly-populated ANN index at this scale, and adding one later is
    # a non-breaking migration.
    op.create_index(
        "ix_knowledge_chunks_company_document",
        "knowledge_chunks",
        ["company_id", "document_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_knowledge_chunks_company_document", table_name="knowledge_chunks")
    op.drop_table("knowledge_chunks")

    op.drop_index("ix_knowledge_documents_company_status", table_name="knowledge_documents")
    op.drop_index("ix_knowledge_documents_company_id", table_name="knowledge_documents")
    op.drop_table("knowledge_documents")

    # Deliberately NOT dropping the vector extension on downgrade — it's
    # a database-wide extension, not something owned by this migration
    # alone, and dropping it could break other things if anything else
    # ever comes to depend on it. Same reasoning most projects use for
    # not dropping pgcrypto/uuid-ossp on downgrade.
