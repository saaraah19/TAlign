"""
Domain events.

A lightweight, dependency-free vocabulary for "something happened" — NOT
an event bus. Nothing here publishes, subscribes, or dispatches. A
producer (e.g. JobService) constructs an event and currently just logs
or returns it. The day a real listener exists — the Workflow Engine
reacting to `JobPublished` to, say, notify a hiring manager — it
consumes this same vocabulary. The Job module doesn't change at all when
that listener is added.

DEPENDENCY RULE: `app/domain/` may be imported by services in any
module (job_service.py, later candidate_service.py, etc). It must never
import from `workflow_engine/`, `agents/`, or `compass/`. Events flow
outward from the domain that raised them; nothing flows back in. This is
what keeps the Job module independent of the Workflow Engine while still
leaving a clean extension point for later.
"""

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(frozen=True, kw_only=True)
class DomainEvent:
    event_name: str
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(frozen=True, kw_only=True)
class JobPublished(DomainEvent):
    """Raised when a Job transitions DRAFT → OPEN."""

    job_id: uuid.UUID
    company_id: uuid.UUID
    event_name: str = "job.published"


@dataclass(frozen=True, kw_only=True)
class JobClosed(DomainEvent):
    """Raised when a Job transitions OPEN → CLOSED."""

    job_id: uuid.UUID
    company_id: uuid.UUID
    event_name: str = "job.closed"


@dataclass(frozen=True, kw_only=True)
class JobArchived(DomainEvent):
    """Raised when a Job transitions CLOSED → ARCHIVED."""

    job_id: uuid.UUID
    company_id: uuid.UUID
    event_name: str = "job.archived"


@dataclass(frozen=True, kw_only=True)
class ApplicationScreeningStarted(DomainEvent):
    """Raised when an Application transitions APPLIED → SCREENING."""

    application_id: uuid.UUID
    company_id: uuid.UUID
    event_name: str = "application.screening_started"


@dataclass(frozen=True, kw_only=True)
class ApplicationInterviewStageEntered(DomainEvent):
    """Raised when an Application transitions SCREENING → INTERVIEW."""

    application_id: uuid.UUID
    company_id: uuid.UUID
    event_name: str = "application.interview_stage_entered"


@dataclass(frozen=True, kw_only=True)
class ApplicationOfferExtended(DomainEvent):
    """Raised when an Application transitions INTERVIEW → OFFER."""

    application_id: uuid.UUID
    company_id: uuid.UUID
    event_name: str = "application.offer_extended"


@dataclass(frozen=True, kw_only=True)
class ApplicationHired(DomainEvent):
    """Raised when an Application transitions OFFER → HIRED."""

    application_id: uuid.UUID
    company_id: uuid.UUID
    event_name: str = "application.hired"


@dataclass(frozen=True, kw_only=True)
class ApplicationRejected(DomainEvent):
    """
    Raised when an Application transitions to REJECTED, from any of
    APPLIED, SCREENING, INTERVIEW, or OFFER. `previous_status` carries
    which stage the rejection happened at, since a future listener (e.g.
    a Workflow Engine step drafting a rejection email) needs that
    context and this is the one Application event that isn't tied to a
    single fixed source state.
    """

    application_id: uuid.UUID
    company_id: uuid.UUID
    previous_status: str
    event_name: str = "application.rejected"
