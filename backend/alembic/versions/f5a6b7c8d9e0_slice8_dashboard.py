"""slice8_dashboard

Revision ID: f5a6b7c8d9e0
Revises: e4f5a6b7c8d9
Create Date: 2026-08-24

Slice 8: Dashboard.

Creates `dashboard_briefs` — caches the LLM-generated Daily Alignment
Brief once per company per calendar day (see
app/models/dashboard_brief.py's docstring for why this is cached rather
than regenerated on every page load). Everything else the Dashboard
shows (pending actions, low-applicant jobs, recent analyses, recent
workflow runs) is deterministic SQL aggregation over existing tables —
no new tables needed for those.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "f5a6b7c8d9e0"
down_revision: str | None = "e4f5a6b7c8d9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "dashboard_briefs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("brief_date", sa.Date(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("recommended_actions", sa.JSON(), nullable=False),
        sa.Column("llm_provider", sa.String(length=50), nullable=True),
        sa.Column("llm_model", sa.String(length=100), nullable=True),
        sa.Column("prompt_version", sa.String(length=50), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.UniqueConstraint(
            "company_id", "brief_date", name="uq_dashboard_briefs_company_date"
        ),
    )
    op.create_index(
        "ix_dashboard_briefs_company_date", "dashboard_briefs", ["company_id", "brief_date"]
    )


def downgrade() -> None:
    op.drop_index("ix_dashboard_briefs_company_date", table_name="dashboard_briefs")
    op.drop_table("dashboard_briefs")
