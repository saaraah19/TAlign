"""slice9c_leave_requests

Revision ID: a1b2c3d4e5f6
Revises: f5a6b7c8d9e0
Create Date: 2026-09-19

Sub-slice 9c: Leave Management.

Creates `leave_requests`. Two-layer validation: this migration encodes
the DB-layer CHECK constraints (valid status/leave_type values,
end_date >= start_date) — the transition-graph and overlap-prevention
rules live in LeaveRequestService, not here, same split as every other
lifecycle in this codebase (see app/models/leave_request.py's module
docstring).

*** IMPORTANT FOR WHOEVER APPLIES THIS LOCALLY ***
`down_revision` below points at `f5a6b7c8d9e0` (slice8_dashboard), the
latest revision on the `main` branch as pulled for this session. Your
local repo has since moved past that (9a, 9a-2, and any other
migrations from work not yet pushed to `main`). Before running
`alembic upgrade head`, update `down_revision` below to your actual
latest local revision id (`alembic heads` will tell you), or this will
create a second, disconnected migration branch.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: str | None = "f5a6b7c8d9e0"  # <-- UPDATE THIS, see docstring above
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "leave_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("leave_type", sa.String(length=20), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("reviewed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reviewed_by"], ["users.id"], ondelete="SET NULL"),
        sa.CheckConstraint(
            "status IN ('pending', 'approved', 'rejected', 'cancelled')",
            name="ck_leave_requests_status_valid",
        ),
        sa.CheckConstraint(
            "leave_type IN ('vacation', 'sick', 'personal')",
            name="ck_leave_requests_leave_type_valid",
        ),
        sa.CheckConstraint(
            "end_date >= start_date",
            name="ck_leave_requests_date_range_valid",
        ),
    )
    op.create_index(
        "ix_leave_requests_employee_id", "leave_requests", ["employee_id"]
    )
    op.create_index(
        "ix_leave_requests_company_id_status", "leave_requests", ["company_id", "status"]
    )


def downgrade() -> None:
    op.drop_index("ix_leave_requests_company_id_status", table_name="leave_requests")
    op.drop_index("ix_leave_requests_employee_id", table_name="leave_requests")
    op.drop_table("leave_requests")
