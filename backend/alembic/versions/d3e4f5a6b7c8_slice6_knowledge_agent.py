"""slice6_knowledge_agent

Revision ID: d3e4f5a6b7c8
Revises: c2d3e4f5a6b7
Create Date: 2026-08-19

Slice 6: Knowledge Agent.

Enables pgvector and creates `knowledge_documents` (identity/lifecycle
— see app/models/knowledge_document.py's docstring for the pipeline
state machine) and `knowledge_chunks` (the pgvector-bearing table
retrieval actually queries — see app/models/knowledge_chunk.py's
docstring for why `company_id` is denormalized directly onto this
table rather than requiring a join through `knowledge_documents` on
every retrieval query).

Embedding dimension fixed at 768 (KnowledgeChunk.EMBEDDING_DIMENSION —
gemini-embedding-001, truncated via Matryoshka Representation Learning
from its native 3072 dimensions). No ANN index (ivfflat/hnsw) yet —
a plain composite (company_id, document_id) index plus seq scan is the
deliberate MVP choice at current data volumes; see the architecture
doc for the reasoning on when that's worth revisiting.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "d3e4f5a6b7c8"
down_revision: str | None = "c2d3e4f5a6b7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

EMBEDDING_DIMENSION = 768


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
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
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

    op.create_table(
        "knowledge_chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=False),
        sa.Column("embedding", Vector(EMBEDDING_DIMENSION), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["document_id"], ["knowledge_documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
    )
    op.create_index(
        "ix_knowledge_chunks_company_document",
        "knowledge_chunks",
        ["company_id", "document_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_knowledge_chunks_company_document", table_name="knowledge_chunks")
    op.drop_table("knowledge_chunks")
    op.drop_table("knowledge_documents")
    # Deliberately NOT dropping the vector extension — other objects in
    # the database (or a later migration) may depend on it, and
    # `CREATE EXTENSION IF NOT EXISTS` on a future upgrade is harmless
    # either way.
