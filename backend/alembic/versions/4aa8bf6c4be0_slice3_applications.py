"""slice3_applications

Revision ID: 4aa8bf6c4be0
Revises: 80dcdaf48a88
Create Date: 2026-07-18

Creates the `applications` table — the central Candidate<->Job
relationship. Two constraints matter most:

  - uq_applications_candidate_job: a candidate cannot apply to the same
    job twice. This is the DB-level half of the "no duplicate
    application" rule; ApplicationService checks it first (a clean
    domain error), this constraint is the last line of defense against
    a race between the check and the insert.
  - ck_applications_status_valid: membership in the six known statuses.
    The transition GRAPH (which status can follow which) is NOT encoded
    here — that lives entirely in ApplicationService._validate_transition,
    same two-layer split used for Job's status in Slice 2.

candidate_id -> users.id is NOT constrained to only reference
account_type='candidate' rows at the DB level (would need a trigger,
since it's a cross-table check) — see app/models/application.py
docstring for why that's an accepted, documented limitation rather than
an oversight.

Handcrafted (no live Postgres instance in the authoring environment) but
matches app/models/application.py exactly — cross-checked via
Base.metadata introspection, same method used for Slices 1 and 2.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "4aa8bf6c4be0"
down_revision: str | None = "80dcdaf48a88"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "applications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("candidate_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="applied"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["candidate_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("candidate_id", "job_id", name="uq_applications_candidate_job"),
        sa.CheckConstraint(
            "status IN ('applied', 'screening', 'interview', 'offer', 'hired', 'rejected')",
            name="ck_applications_status_valid",
        ),
    )
    op.create_index("ix_applications_candidate_id", "applications", ["candidate_id"])
    op.create_index("ix_applications_job_id", "applications", ["job_id"])
    op.create_index("ix_applications_company_id", "applications", ["company_id"])
    op.create_index("ix_applications_company_status", "applications", ["company_id", "status"])


def downgrade() -> None:
    op.drop_index("ix_applications_company_status", table_name="applications")
    op.drop_index("ix_applications_company_id", table_name="applications")
    op.drop_index("ix_applications_job_id", table_name="applications")
    op.drop_index("ix_applications_candidate_id", table_name="applications")
    op.drop_table("applications")
