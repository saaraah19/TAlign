"""slice4_1_job_salary_currency

Revision ID: b1c2d3e4f5a6
Revises: a78ee5b3422c
Create Date: 2026-07-26

Adds `jobs.salary_currency` — a label only, no conversion logic
anywhere in the codebase. Existing rows default to 'USD' so this is a
purely additive, backward-compatible change; no other column is
touched. See app/models/job.py's `Currency` enum docstring.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "b1c2d3e4f5a6"
down_revision: str | None = "a78ee5b3422c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "jobs",
        sa.Column("salary_currency", sa.String(length=3), nullable=False, server_default="USD"),
    )
    op.create_check_constraint(
        "ck_jobs_salary_currency_valid",
        "jobs",
        "salary_currency IN ('USD', 'EUR', 'GBP', 'CAD')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_jobs_salary_currency_valid", "jobs", type_="check")
    op.drop_column("jobs", "salary_currency")
