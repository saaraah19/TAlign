"""
JobService.

Owns every business rule around Jobs, including the status lifecycle.
This is deliberately NOT a generic, reusable state-machine framework —
`_ALLOWED_TRANSITIONS` is a plain dict, private to this file, encoding
exactly one domain's rules. If a second entity later needs its own
lifecycle (e.g. Application: applied -> screening -> interview -> ...),
it gets its own small dict in its own service, not a shared abstraction
imported from here. Reaching for a generic engine before a second real
use case exists would be exactly the kind of premature abstraction
CLAUDE.md warns against.

Independence from the Workflow Engine: this file has zero imports from
`app.workflow_engine` or `app.agents`. Status transitions emit a
`DomainEvent` (see app/domain/events.py) that a future Workflow Engine
listener could react to — but JobService doesn't know or care whether
anything is listening. It would behave identically with zero consumers.
"""

import uuid

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    AuthorizationError,
    InvalidJobStatusTransitionError,
    NotFoundError,
)
from app.domain.events import DomainEvent, JobArchived, JobClosed, JobPublished
from app.models.job import Job, JobStatus
from app.models.user import User
from app.repositories.job_repository import JobRepository

logger = structlog.get_logger(__name__)

# The entire transition graph, in one place. DRAFT -> OPEN -> CLOSED ->
# ARCHIVED, linear, no skipping, no going backward — exactly the
# lifecycle specified for Slice 2. Extending this later (e.g. allowing
# OPEN -> DRAFT to "unpublish") is a one-line change here, reviewed
# deliberately rather than falling out of a generic engine's defaults.
_ALLOWED_TRANSITIONS: dict[JobStatus, set[JobStatus]] = {
    JobStatus.DRAFT: {JobStatus.OPEN},
    JobStatus.OPEN: {JobStatus.CLOSED},
    JobStatus.CLOSED: {JobStatus.ARCHIVED},
    JobStatus.ARCHIVED: set(),
}

# Which event fires on which transition. Kept as a lookup rather than an
# if/elif chain so adding a transition and forgetting its event is a
# KeyError at test time, not a silent gap.
_TRANSITION_EVENTS: dict[tuple[JobStatus, JobStatus], type[DomainEvent]] = {
    (JobStatus.DRAFT, JobStatus.OPEN): JobPublished,
    (JobStatus.OPEN, JobStatus.CLOSED): JobClosed,
    (JobStatus.CLOSED, JobStatus.ARCHIVED): JobArchived,
}


class JobService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._jobs = JobRepository(db)

    async def create_job(
        self,
        *,
        acting_user: User,
        title: str,
        description: str,
        employment_type: str,
        location: str | None,
        salary_min: int | None,
        salary_max: int | None,
        salary_currency: str = "USD",
        required_skills: list[str] | None = None,
        preferred_skills: list[str] | None = None,
        min_years_experience: int | None = None,
    ) -> Job:
        self._assert_internal_with_company(acting_user)

        job = Job(
            company_id=acting_user.company_id,
            created_by=acting_user.id,
            title=title,
            description=description,
            employment_type=employment_type,
            location=location,
            salary_min=salary_min,
            salary_max=salary_max,
            salary_currency=salary_currency,
            status=JobStatus.DRAFT.value,
            required_skills=required_skills or [],
            preferred_skills=preferred_skills or [],
            min_years_experience=min_years_experience,
        )
        job = await self._jobs.create(job)
        await self._db.commit()
        return job

    async def get_job(self, *, job_id: uuid.UUID, acting_user: User) -> Job:
        self._assert_internal_with_company(acting_user)
        job = await self._jobs.get_by_id_for_company(job_id, acting_user.company_id)
        if job is None:
            raise NotFoundError("Job not found.")
        return job

    async def list_jobs(
        self,
        *,
        acting_user: User,
        status: str | None,
        page: int,
        page_size: int,
    ) -> tuple[list[Job], int]:
        self._assert_internal_with_company(acting_user)
        return await self._jobs.list_for_company(
            acting_user.company_id, status=status, page=page, page_size=page_size
        )

    # --- Public, unauthenticated reads (candidate-facing job browsing) ---
    # Deliberately separate from the company-scoped methods above: these
    # cross every company's boundary on purpose, restricted only to jobs
    # with status=OPEN. No RBAC guard applies to these two methods —
    # app/api/v1/public_jobs.py calls them with no `Depends(require_roles(...))`
    # at all.

    async def list_open_jobs(self, *, page: int, page_size: int) -> tuple[list[Job], int]:
        return await self._jobs.list_open(page=page, page_size=page_size)

    async def get_open_job(self, *, job_id: uuid.UUID) -> Job:
        job = await self._jobs.get_by_id(job_id)
        if job is None or job.status != JobStatus.OPEN.value:
            raise NotFoundError("Job not found.")
        return job

    async def update_job(
        self,
        *,
        job_id: uuid.UUID,
        acting_user: User,
        **fields: str | int | None,
    ) -> Job:
        job = await self.get_job(job_id=job_id, acting_user=acting_user)
        if job.status == JobStatus.ARCHIVED.value:
            raise InvalidJobStatusTransitionError("Archived jobs can no longer be edited.")

        for field_name, value in fields.items():
            if value is not None:
                setattr(job, field_name, value)

        await self._db.commit()
        return job

    async def delete_job(self, *, job_id: uuid.UUID, acting_user: User) -> None:
        """Only DRAFT jobs may be hard-deleted — anything published has
        a real lifecycle to follow (close, then archive) instead."""
        job = await self.get_job(job_id=job_id, acting_user=acting_user)
        if job.status != JobStatus.DRAFT.value:
            raise InvalidJobStatusTransitionError(
                "Only draft jobs can be deleted. Close and archive published jobs instead."
            )
        await self._jobs.delete(job)
        await self._db.commit()

    async def transition_status(
        self,
        *,
        job_id: uuid.UUID,
        target_status: JobStatus,
        acting_user: User,
    ) -> tuple[Job, DomainEvent | None]:
        job = await self.get_job(job_id=job_id, acting_user=acting_user)
        current_status = JobStatus(job.status)

        self._validate_transition(current_status, target_status)

        job.status = target_status.value
        await self._db.commit()

        event_cls = _TRANSITION_EVENTS.get((current_status, target_status))
        event: DomainEvent | None = None
        if event_cls is not None:
            event = event_cls(job_id=job.id, company_id=job.company_id)
            # Logged, not published — see module docstring. This is the
            # seam a future Workflow Engine listener attaches to; today
            # it's observability only.
            logger.info(
                "domain_event",
                event_name=event.event_name,
                job_id=str(job.id),
                company_id=str(job.company_id),
            )

        return job, event

    @staticmethod
    def _validate_transition(current: JobStatus, target: JobStatus) -> None:
        allowed = _ALLOWED_TRANSITIONS.get(current, set())
        if target not in allowed:
            raise InvalidJobStatusTransitionError(
                f"Cannot transition a job from '{current.value}' to '{target.value}'."
            )

    @staticmethod
    def _assert_internal_with_company(user: User) -> None:
        # Defensive check: RBAC at the API layer already restricts these
        # endpoints to internal roles, but a service should never trust
        # that a caller enforced its own preconditions correctly.
        if user.company_id is None:
            raise AuthorizationError("This action requires an internal company account.")
