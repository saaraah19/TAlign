"""
Resume model.

Owned by a candidate (`User` with account_type=candidate — see Slice 1/3),
NOT by any single Application. One candidate can upload several resumes;
one resume can be attached to several Applications across different
companies. This is what makes ParsedResume reuse possible (see that
model's docstring): parse a resume's structured content once, reuse it
across every job the candidate applies with that resume, and only run a
fresh LLM call for the job-specific alignment reasoning each time.

`raw_text` is populated by a DETERMINISTIC step (pypdf/python-docx, see
app/utils/document_text_extraction.py) — no LLM involved in getting from
file bytes to plain text. The LLM enters one step later, turning that
raw text into structured skills/experience (ParsedResume).
"""

import uuid
from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class ResumeStatus(StrEnum):
    UPLOADED = "uploaded"
    PARSE_FAILED = "parse_failed"  # deterministic text-extraction step failed
    TEXT_READY = "text_ready"  # raw_text populated, ready for LLM structuring


class Resume(Base):
    __tablename__ = "resumes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)

    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=ResumeStatus.UPLOADED)
    parse_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    candidate: Mapped["User"] = relationship()

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Resume id={self.id} candidate_id={self.candidate_id} status={self.status}>"
