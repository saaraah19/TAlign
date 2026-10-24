"""slice1_authentication_identity

Revision ID: a9bb0d24163b
Revises:
Create Date: 2026-07-18

Creates the Authentication & Identity schema: companies, roles,
user_roles, users. Seeds the five roles from app.core.roles.Role so
AuthService can resolve them immediately after migration.

This migration was handcrafted (no live Postgres instance was available
to run `alembic revision --autogenerate` against in the authoring
environment) but was written to match app/models/*.py exactly — verify
with `alembic check` once a real database is available, before applying
in any shared environment.
"""

from collections.abc import Sequence
import uuid

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "a9bb0d24163b"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --- companies ---
    op.create_table(
        "companies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("logo_url", sa.String(length=512), nullable=True),
        sa.Column("industry", sa.String(length=255), nullable=True),
        sa.Column("size", sa.String(length=50), nullable=True),
        sa.Column("country", sa.String(length=100), nullable=True),
        sa.Column("timezone", sa.String(length=64), nullable=False, server_default="UTC"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_unique_constraint("uq_companies_slug", "companies", ["slug"])
    op.create_index("ix_companies_slug", "companies", ["slug"])

    # --- roles ---
    op.create_table(
        "roles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
    )
    op.create_unique_constraint("uq_roles_name", "roles", ["name"])

    # --- users ---
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("account_type", sa.String(length=20), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("first_name", sa.String(length=100), nullable=False),
        sa.Column("last_name", sa.String(length=100), nullable=False),
        sa.Column("avatar_url", sa.String(length=512), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.CheckConstraint(
            "(account_type = 'candidate' AND company_id IS NULL) "
            "OR (account_type = 'internal' AND company_id IS NOT NULL)",
            name="ck_users_company_assignment",
        ),
    )
    op.create_unique_constraint("uq_users_email", "users", ["email"])
    op.create_index("ix_users_email", "users", ["email"])

    # --- user_roles ---
    op.create_table(
        "user_roles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", "role_id", name="uq_user_roles_user_role"),
    )

    # --- seed roles (matches app.core.roles.Role exactly) ---
    roles_table = sa.table(
        "roles",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("name", sa.String),
        sa.column("description", sa.String),
    )
    op.bulk_insert(
        roles_table,
        [
            {"id": uuid.uuid4(), "name": "admin", "description": "Company administrator"},
            {"id": uuid.uuid4(), "name": "recruiter", "description": "Talent acquisition"},
            {"id": uuid.uuid4(), "name": "hiring_manager", "description": "Reviews and approves candidates"},
            {"id": uuid.uuid4(), "name": "employee", "description": "Internal company employee"},
            {"id": uuid.uuid4(), "name": "candidate", "description": "Platform-wide job applicant"},
        ],
    )


def downgrade() -> None:
    op.drop_table("user_roles")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_constraint("uq_users_email", "users", type_="unique")
    op.drop_table("users")
    op.drop_constraint("uq_roles_name", "roles", type_="unique")
    op.drop_table("roles")
    op.drop_index("ix_companies_slug", table_name="companies")
    op.drop_constraint("uq_companies_slug", "companies", type_="unique")
    op.drop_table("companies")
