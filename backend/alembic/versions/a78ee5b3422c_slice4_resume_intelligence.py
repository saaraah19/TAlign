"""slice4_resume_intelligence

Revision ID: a78ee5b3422c
Revises: 4aa8bf6c4be0
Create Date: 2026-07-19

Slice 4: Resume Intelligence Agent.

  - jobs: adds required_skills, preferred_skills, min_years_experience
    (the recruiter-authored OFFICIAL scoring criteria — see
    app/models/job.py).
  - resumes: candidate-owned uploaded files, reusable across applications.
  - parsed_resumes: LLM-extracted structured content, versioned, reused
    across applications via the same resume.
  - resume_analyses: the alignment analysis, one row per attempt, never
    updated after creation — re-analysis always inserts a new row.
  - applications: adds resume_id (the currently-selected resume for this
    application — see app/models/application.py's docstring on why this
    is not redundant with resume_analyses.parsed_resume_id).

Handcrafted (no live Postgres instance in the authoring environment) but
matches app/models/*.py exactly — cross-checked via Base.metadata
introspection, same method used for Slices 1-3.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "a78ee5b3422c"
down_revision: str | None = "4aa8bf6c4be0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --- jobs: recruiter-authored scoring criteria ---
    op.add_column(
        "jobs",
        sa.Column(
            "required_skills",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
    )
    op.add_column(
        "jobs",
        sa.Column(
            "preferred_skills",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
    )
    op.add_column("jobs", sa.Column("min_years_experience", sa.Integer(), nullable=True))

    # --- resumes ---
    op.create_table(
        "resumes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("candidate_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("file_path", sa.String(length=1024), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=100), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="uploaded"),
        sa.Column("parse_error", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["candidate_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_resumes_candidate_id", "resumes", ["candidate_id"])

    # --- parsed_resumes ---
    op.create_table(
        "parsed_resumes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("resume_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "extracted_skills",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "experience_entries",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column("total_years_experience", sa.Float(), nullable=True),
        sa.Column(
            "education",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "certifications",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column("llm_provider", sa.String(length=50), nullable=False),
        sa.Column("llm_model", sa.String(length=100), nullable=False),
        sa.Column("prompt_version", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["resume_id"], ["resumes.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_parsed_resumes_resume_id", "parsed_resumes", ["resume_id"])
    op.create_index("ix_parsed_resumes_resume_status", "parsed_resumes", ["resume_id", "status"])

    # --- resume_analyses ---
    op.create_table(
        "resume_analyses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("parsed_resume_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("overall_score", sa.Float(), nullable=True),
        sa.Column("required_skills_score_pct", sa.Float(), nullable=True),
        sa.Column("preferred_skills_score_pct", sa.Float(), nullable=True),
        sa.Column("experience_score_pct", sa.Float(), nullable=True),
        sa.Column("scoring_algorithm_version", sa.String(length=50), nullable=True),
        sa.Column(
            "required_skills_result",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "preferred_skills_result",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column("experience_fit", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "matched_skills",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "missing_skills",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "strengths",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "potential_concerns",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("llm_provider", sa.String(length=50), nullable=True),
        sa.Column("llm_model", sa.String(length=100), nullable=True),
        sa.Column("prompt_version", sa.String(length=50), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("analyzed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["parsed_resume_id"], ["parsed_resumes.id"], ondelete="CASCADE"),
        sa.CheckConstraint(
            "status IN ('pending', 'completed', 'failed')",
            name="ck_resume_analyses_status_valid",
        ),
    )
    op.create_index("ix_resume_analyses_application_id", "resume_analyses", ["application_id"])
    op.create_index(
        "ix_resume_analyses_application_status", "resume_analyses", ["application_id", "status"]
    )

    # --- applications: currently-selected resume ---
    op.add_column(
        "applications", sa.Column("resume_id", postgresql.UUID(as_uuid=True), nullable=True)
    )
    op.create_foreign_key(
        "fk_applications_resume_id",
        "applications",
        "resumes",
        ["resume_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_applications_resume_id", "applications", type_="foreignkey")
    op.drop_column("applications", "resume_id")

    op.drop_index("ix_resume_analyses_application_status", table_name="resume_analyses")
    op.drop_index("ix_resume_analyses_application_id", table_name="resume_analyses")
    op.drop_table("resume_analyses")

    op.drop_index("ix_parsed_resumes_resume_status", table_name="parsed_resumes")
    op.drop_index("ix_parsed_resumes_resume_id", table_name="parsed_resumes")
    op.drop_table("parsed_resumes")

    op.drop_index("ix_resumes_candidate_id", table_name="resumes")
    op.drop_table("resumes")

    op.drop_column("jobs", "min_years_experience")
    op.drop_column("jobs", "preferred_skills")
    op.drop_column("jobs", "required_skills")
