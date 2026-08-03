"""slice5_communication_emails

Revision ID: c2d3e4f5a6b7
Revises: b1c2d3e4f5a6
Create Date: 2026-07-27

Slice 5: Communication Agent.

Creates `emails` — one row per drafted/sent email, DRAFT/SENT lifecycle
only (see app/models/email.py's docstring). No real email sending
infrastructure exists; "sent" is the recruiter marking that they sent
it through their own tooling.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "c2d3e4f5a6b7"
down_revision: str | None = "b1c2d3e4f5a6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "emails",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("email_type", sa.String(length=30), nullable=False),
        sa.Column("status", sa.String(length=10), nullable=False, server_default="draft"),
        sa.Column("recipient_email", sa.String(length=255), nullable=False),
        sa.Column("subject", sa.String(length=255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("llm_provider", sa.String(length=50), nullable=True),
        sa.Column("llm_model", sa.String(length=100), nullable=True),
        sa.Column("prompt_version", sa.String(length=50), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.CheckConstraint(
            "email_type IN ('rejection', 'interview_invitation')",
            name="ck_emails_type_valid",
        ),
        sa.CheckConstraint("status IN ('draft', 'sent')", name="ck_emails_status_valid"),
    )
    op.create_index("ix_emails_application_id", "emails", ["application_id"])
    op.create_index("ix_emails_company_id", "emails", ["company_id"])
    op.create_index(
        "ix_emails_application_type_status", "emails", ["application_id", "email_type", "status"]
    )


def downgrade() -> None:
    op.drop_index("ix_emails_application_type_status", table_name="emails")
    op.drop_index("ix_emails_company_id", table_name="emails")
    op.drop_index("ix_emails_application_id", table_name="emails")
    op.drop_table("emails")
