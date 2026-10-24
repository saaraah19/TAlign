"""slice2_jobs

Revision ID: 80dcdaf48a88
Revises: a9bb0d24163b
Create Date: 2026-07-18

Creates the `jobs` table. The status transition GRAPH (DRAFT -> OPEN ->
CLOSED -> ARCHIVED) is enforced in JobService, not the database — the DB
only constrains membership in the valid status set via
ck_jobs_status_valid, mirroring the Slice 1 two-layer pattern applied to
Job instead of User.

Handcrafted (no live Postgres instance available in the authoring
environment) but matches app/models/job.py exactly — cross-checked via
Base.metadata introspection, see docs/02_slice2_jobs.md.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "80dcdaf48a88"
down_revision: str | None = "a9bb0d24163b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("employment_type", sa.String(length=20), nullable=False),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("salary_min", sa.Integer(), nullable=True),
        sa.Column("salary_max", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="draft"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.CheckConstraint(
            "status IN ('draft', 'open', 'closed', 'archived')", name="ck_jobs_status_valid"
        ),
        sa.CheckConstraint(
            "employment_type IN ('full_time', 'part_time', 'contract', 'internship')",
            name="ck_jobs_employment_type_valid",
        ),
        sa.CheckConstraint(
            "salary_min IS NULL OR salary_max IS NULL OR salary_min <= salary_max",
            name="ck_jobs_salary_range_valid",
        ),
    )
    op.create_index("ix_jobs_company_id", "jobs", ["company_id"])
    op.create_index("ix_jobs_status", "jobs", ["status"])


def downgrade() -> None:
    op.drop_index("ix_jobs_status", table_name="jobs")
    op.drop_index("ix_jobs_company_id", table_name="jobs")
    op.drop_table("jobs")
