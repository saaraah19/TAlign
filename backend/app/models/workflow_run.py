"""
WorkflowRun model.

A write-once audit row persisted by the Workflow Engine after every
trigger attempt — not just a structlog line. Two reasons this earns
real persistence rather than following domain events' "vocabulary, not
a bus" precedent:

  1. The Product Book leans hard on transparency (Decision Log, Audit
     Log, "explain every important decision" as a named Product
     Principle in CLAUDE.md) — a workflow that silently ran and left no
     queryable trace undercuts that.
  2. The next slice (Dashboard) explicitly wants "recent AI analyses"
     and Compass recommendations surfaced — this table is the natural
     read for "what workflows ran recently, did they succeed."

Three possible outcomes, not two:

    SUCCESS — every step completed.
    FAILED  — a step raised; `failed_step` names which one,
              `completed_steps` still records everything that finished
              before the failure (partial-completion tracking).
    SKIPPED — the workflow's idempotency guard found this trigger
              entity had already been processed (e.g. an Employee
              already exists for this application_id) and did no work.
              Recorded so a duplicate trigger is observable, not
              silent — distinguishing "ran and did nothing new" from
              "never ran" matters for anyone reading this table later.

No retry/replay logic exists — this is a log, not a queue. Re-running a
workflow means triggering it again through its normal entry point,
which the idempotency guard makes safe.
"""

import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class WorkflowRunStatus(StrEnum):
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class WorkflowRun(Base):
    __tablename__ = "workflow_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )

    workflow_name: Mapped[str] = mapped_column(String(100), nullable=False)
    #: What triggered this run, e.g. "application" / the Application's id.
    #: Kept generic (not a hard FK) since future workflows may trigger
    #: off entities other than Application (a Job closing, etc).
    trigger_entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    trigger_entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    status: Mapped[str] = mapped_column(String(20), nullable=False)
    completed_steps: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    #: Which step raised, when status == FAILED. NULL for SUCCESS/SKIPPED.
    failed_step: Mapped[str | None] = mapped_column(String(100), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<WorkflowRun id={self.id} workflow={self.workflow_name} status={self.status}>"
