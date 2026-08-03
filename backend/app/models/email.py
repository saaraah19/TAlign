"""
Email model.

Persists every drafted/sent communication tied to an Application. Two
lifecycle states only, deliberately simple for the MVP:

    DRAFT  -> mutable. The recruiter can regenerate (fresh LLM call,
              overwrites this row) or hand-edit subject/body freely.
    SENT   -> immutable. Once marked sent, no further edits or
              regeneration are permitted — this is now a historical
              record of what was actually communicated, same "never
              silently rewrite history" discipline as ResumeAnalysis,
              just expressed as a state transition instead of an
              insert-only table (drafts genuinely are meant to be
              edited in place; only the SENT state is history).

`email_type` distinguishes which template/prompt produced it —
currently REJECTION and INTERVIEW_INVITATION only (see
docs/05_slice5_communication_agent.md for the two-type MVP scope
decision; follow-up/reminder/offer/onboarding are deferred).

No real email sending happens anywhere in this codebase (no SMTP/Gmail
integration) — "send" here means the recruiter has copied/sent it
through their own tooling and is marking it as such for the record.
"""

import uuid
from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.application import Application
    from app.models.user import User


class EmailType(StrEnum):
    REJECTION = "rejection"
    INTERVIEW_INVITATION = "interview_invitation"


class EmailStatus(StrEnum):
    DRAFT = "draft"
    SENT = "sent"


class Email(Base):
    __tablename__ = "emails"
    __table_args__ = (
        CheckConstraint(
            "email_type IN ('rejection', 'interview_invitation')",
            name="ck_emails_type_valid",
        ),
        CheckConstraint("status IN ('draft', 'sent')", name="ck_emails_status_valid"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False
    )
    #: Denormalized for company-scoped queries without a join through
    #: Application — same pattern as Application.company_id itself.
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    email_type: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(10), nullable=False, default=EmailStatus.DRAFT)

    #: Denormalized at creation time, not a live join to User.email —
    #: if the candidate's email later changes, this row should still
    #: reflect who it was actually addressed to at send time.
    recipient_email: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)

    # --- Versioning / provenance (same discipline as ParsedResume/ResumeAnalysis) ---
    llm_provider: Mapped[str | None] = mapped_column(String(50), nullable=True)
    llm_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    prompt_version: Mapped[str | None] = mapped_column(String(50), nullable=True)

    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    application: Mapped["Application"] = relationship()
    creator: Mapped["User | None"] = relationship()

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Email id={self.id} type={self.email_type} status={self.status}>"
