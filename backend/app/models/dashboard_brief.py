"""
DashboardBrief model.

Caches the Daily Alignment Brief exactly once per company per calendar
day — regenerating it on every Dashboard page load would mean an LLM
call (cost, latency) on every visit, and since LLM output isn't
deterministic, refreshing the page would show a subtly different brief
each time, which feels broken for something literally named "Daily."
`DashboardService.get_or_generate_daily_brief` checks this table first;
only generates and inserts a new row if none exists for
(company_id, brief_date) yet.

`brief_date` is a plain Date, not a timestamp — deliberately coarse.
"Today" is defined server-side (UTC calendar date), not per-user
timezone; a future V2 could refine this, not worth the complexity now.

`recommended_actions` is the one part of this row that's genuinely
LLM-generated content (the summary prose, plus a short prioritized
action list) — everything else surfaced on the Dashboard (pending
applications, low-applicant jobs, recent analyses) is deterministic SQL
aggregation computed fresh on every request by DashboardService, never
cached, never LLM-touched. This split matters: the LLM only ever
synthesizes prose and suggestions on top of already-computed facts: it
never computes a score, a count, or a threshold itself.
"""

import uuid
from datetime import date, datetime
from typing import Any

from sqlalchemy import JSON, Date, DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class DashboardBrief(Base):
    __tablename__ = "dashboard_briefs"
    __table_args__ = (
        UniqueConstraint("company_id", "brief_date", name="uq_dashboard_briefs_company_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    brief_date: Mapped[date] = mapped_column(Date, nullable=False)

    summary: Mapped[str] = mapped_column(Text, nullable=False)
    #: list[{"label": str, "application_id": str | None}] — the LLM's
    #: own suggested next actions ("Review Ahmed", "Follow up Lina").
    #: application_id is a plain string (not FK-enforced) since a
    #: recommendation may not always point at a specific application.
    recommended_actions: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON, nullable=False, default=list
    )

    llm_provider: Mapped[str | None] = mapped_column(String(50), nullable=True)
    llm_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    prompt_version: Mapped[str | None] = mapped_column(String(50), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<DashboardBrief id={self.id} company_id={self.company_id} date={self.brief_date}>"
