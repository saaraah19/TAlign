"""slice7_workflow_engine

Revision ID: e4f5a6b7c8d9
Revises: d3e4f5a6b7c8
Create Date: 2026-08-20

Slice 7: Workflow Engine.

Creates `employees` (thin MVP record, see app/models/employee.py's
docstring — NOT the Employee Portal), `onboarding_tasks` (flat
checklist), and `workflow_runs` (write-once audit log of workflow
trigger attempts). Also extends `emails.ck_emails_type_valid` to allow
`onboarding_welcome`, the new email type the hire workflow drafts.

`employees.application_id` is UNIQUE — this is the DB-layer half of the
hire workflow's idempotency guarantee (service-layer half lives in
EmployeeService, which checks before inserting).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "e4f5a6b7c8d9"
down_revision: str | None = "d3e4f5a6b7c8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "employees",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("first_name", sa.String(length=100), nullable=False),
        sa.Column("last_name", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("job_title", sa.String(length=255), nullable=False),
        sa.Column("hire_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
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
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.CheckConstraint("status IN ('active')", name="ck_employees_status_valid"),
    )

    op.create_table(
        "onboarding_tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("completed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"], ondelete="CASCADE"),
    )
    op.create_index(
        "ix_onboarding_tasks_employee_id", "onboarding_tasks", ["employee_id"]
    )

    op.create_table(
        "workflow_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("workflow_name", sa.String(length=100), nullable=False),
        sa.Column("trigger_entity_type", sa.String(length=50), nullable=False),
        sa.Column("trigger_entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("completed_steps", sa.JSON(), nullable=False),
        sa.Column("failed_step", sa.String(length=100), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
    )
    op.create_index(
        "ix_workflow_runs_trigger",
        "workflow_runs",
        ["trigger_entity_type", "trigger_entity_id"],
    )

    op.drop_constraint("ck_emails_type_valid", "emails", type_="check")
    op.create_check_constraint(
        "ck_emails_type_valid",
        "emails",
        "email_type IN ('rejection', 'interview_invitation', 'onboarding_welcome')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_emails_type_valid", "emails", type_="check")
    op.create_check_constraint(
        "ck_emails_type_valid",
        "emails",
        "email_type IN ('rejection', 'interview_invitation')",
    )

    op.drop_index("ix_workflow_runs_trigger", table_name="workflow_runs")
    op.drop_table("workflow_runs")

    op.drop_index("ix_onboarding_tasks_employee_id", table_name="onboarding_tasks")
    op.drop_table("onboarding_tasks")

    op.drop_table("employees")
