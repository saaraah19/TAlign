"""
ApplicationService.

Owns every business rule around Applications: submitting one, reading
them (candidate's own, or a company's pipeline), and moving one through
its status lifecycle.

Flow for every mutation, exactly as specified:

    User action -> ApplicationService -> validate -> persist -> return

No Workflow Engine, no Compass, no Agents anywhere in this file — same
independence rule as JobService, checked mechanically in
tests/test_application_workflow_independence.py.

Status lifecycle (linear with one terminal branch):

    APPLIED -> SCREENING -> INTERVIEW -> OFFER -> HIRED
       |          |            |          |
       +----------+------------+----------+--> REJECTED

HIRED and REJECTED are both terminal. Enforced the same two-layer way as
Job: DB CHECK constrains valid status VALUES only; `_validate_transition`
here is the only place the transition GRAPH is encoded.

Repositories are injected with defaults (`application_repository: ... =
None`) specifically so tests can substitute fakes/mocks without a live
database — see tests/test_application_service_rules.py, which exercises
the duplicate-application and job-not-open checks this way.
"""

import uuid

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    DuplicateApplicationError,
    InvalidApplicationStatusTransitionError,
    InvalidCandidateError,
    JobNotOpenForApplicationsError,
    NotFoundError,
    ResumeNotOwnedError,
)
from app.core.roles import AccountType
from app.domain.events import (
    ApplicationHired,
    ApplicationInterviewStageEntered,
    ApplicationOfferExtended,
    ApplicationRejected,
    ApplicationScreeningStarted,
    DomainEvent,
)
from app.models.application import Application, ApplicationStatus
from app.models.job import JobStatus
from app.models.user import User
from app.repositories.application_repository import ApplicationRepository
from app.repositories.job_repository import JobRepository
from app.repositories.resume_repository import ResumeRepository

logger = structlog.get_logger(__name__)

# The entire transition graph. Linear progression APPLIED -> SCREENING ->
# INTERVIEW -> OFFER -> HIRED, with REJECTED reachable as a terminal
# branch from any non-terminal state. HIRED and REJECTED have no
# outgoing transitions — both terminal for the MVP, matching the exact
# lifecycle specified for Slice 3.
_ALLOWED_TRANSITIONS: dict[ApplicationStatus, set[ApplicationStatus]] = {
    ApplicationStatus.APPLIED: {ApplicationStatus.SCREENING, ApplicationStatus.REJECTED},
    ApplicationStatus.SCREENING: {ApplicationStatus.INTERVIEW, ApplicationStatus.REJECTED},
    ApplicationStatus.INTERVIEW: {ApplicationStatus.OFFER, ApplicationStatus.REJECTED},
    ApplicationStatus.OFFER: {ApplicationStatus.HIRED, ApplicationStatus.REJECTED},
    ApplicationStatus.HIRED: set(),
    ApplicationStatus.REJECTED: set(),
}

_FORWARD_TRANSITION_EVENTS: dict[
    tuple[ApplicationStatus, ApplicationStatus], type[DomainEvent]
] = {
    (ApplicationStatus.APPLIED, ApplicationStatus.SCREENING): ApplicationScreeningStarted,
    (ApplicationStatus.SCREENING, ApplicationStatus.INTERVIEW): ApplicationInterviewStageEntered,
    (ApplicationStatus.INTERVIEW, ApplicationStatus.OFFER): ApplicationOfferExtended,
    (ApplicationStatus.OFFER, ApplicationStatus.HIRED): ApplicationHired,
}


class ApplicationService:
    def __init__(
        self,
        db: AsyncSession,
        application_repository: ApplicationRepository | None = None,
        job_repository: JobRepository | None = None,
        resume_repository: ResumeRepository | None = None,
    ) -> None:
        self._db = db
        self._applications = application_repository or ApplicationRepository(db)
        self._jobs = job_repository or JobRepository(db)
        self._resumes = resume_repository or ResumeRepository(db)

    # --- Submission ---

    async def apply(self, *, candidate: User, job_id: uuid.UUID) -> Application:
        self._assert_valid_candidate(candidate)

        job = await self._jobs.get_by_id(job_id)
        if job is None:
            raise NotFoundError("Job not found.")
        self._assert_job_is_open(job.status)

        already_applied = await self._applications.exists_for_candidate_and_job(
            candidate.id, job_id
        )
        if already_applied:
            raise DuplicateApplicationError("You have already applied to this job.")

        application = Application(
            candidate_id=candidate.id,
            job_id=job.id,
            company_id=job.company_id,  # denormalized, immutable — see model docstring
            status=ApplicationStatus.APPLIED.value,
        )
        application = await self._applications.create(application)
        await self._db.commit()
        return application

    # --- Resume attachment (Slice 4) ---

    async def attach_resume(
        self, *, application_id: uuid.UUID, resume_id: uuid.UUID, candidate: User
    ) -> Application:
        """
        Sets (or replaces) the application's currently-attached resume.
        Always allowed while the candidate owns both the application and
        the resume — per product decision, calling this endpoint IS the
        "explicit user action" that authorizes creating a fresh analysis
        version if one already exists; the API layer schedules that
        background re-run immediately after this returns (see
        app/api/v1/applications.py).

        Deliberately does NOT branch on whether a completed
        ResumeAnalysis already exists — one code path handles both "no
        analysis yet" and "replacing an already-analyzed resume"
        identically, avoiding two subtly-different branches to maintain
        for what is, from this method's point of view, the same action:
        set the pointer, let the caller decide to (re-)trigger analysis.
        """
        self._assert_valid_candidate(candidate)

        application = await self._applications.get_by_id_for_candidate(
            application_id, candidate.id
        )
        if application is None:
            raise NotFoundError("Application not found.")

        resume = await self._resumes.get_by_id_for_candidate(resume_id, candidate.id)
        if resume is None:
            raise ResumeNotOwnedError("Resume not found.")

        application.resume_id = resume.id
        await self._db.commit()
        return application

    # --- Candidate-facing reads ---

    async def get_my_application(
        self, *, application_id: uuid.UUID, candidate: User
    ) -> Application:
        self._assert_valid_candidate(candidate)
        application = await self._applications.get_by_id_for_candidate(
            application_id, candidate.id
        )
        if application is None:
            raise NotFoundError("Application not found.")
        return application

    async def list_my_applications(
        self, *, candidate: User, page: int, page_size: int
    ) -> tuple[list[Application], int]:
        self._assert_valid_candidate(candidate)
        return await self._applications.list_for_candidate(
            candidate.id, page=page, page_size=page_size
        )

    # --- Recruiter-facing reads (company pipeline) ---

    async def get_application_for_company(
        self, *, application_id: uuid.UUID, acting_user: User
    ) -> Application:
        application = await self._applications.get_by_id_for_company(
            application_id, acting_user.company_id
        )
        if application is None:
            raise NotFoundError("Application not found.")
        return application

    async def list_applications_for_company(
        self,
        *,
        acting_user: User,
        job_id: uuid.UUID | None,
        status: str | None,
        page: int,
        page_size: int,
    ) -> tuple[list[Application], int]:
        return await self._applications.list_for_company(
            acting_user.company_id, job_id=job_id, status=status, page=page, page_size=page_size
        )

    # --- Status transitions ---

    async def transition_status(
        self,
        *,
        application_id: uuid.UUID,
        target_status: ApplicationStatus,
        acting_user: User,
    ) -> tuple[Application, DomainEvent | None]:
        application = await self.get_application_for_company(
            application_id=application_id, acting_user=acting_user
        )
        current_status = ApplicationStatus(application.status)

        self._validate_transition(current_status, target_status)

        application.status = target_status.value
        await self._db.commit()

        event = self._build_event(current_status, target_status, application)
        if event is not None:
            logger.info(
                "domain_event",
                event_name=event.event_name,
                application_id=str(application.id),
                company_id=str(application.company_id),
            )

        return application, event

    @staticmethod
    def _build_event(
        current: ApplicationStatus, target: ApplicationStatus, application: Application
    ) -> DomainEvent | None:
        if target is ApplicationStatus.REJECTED:
            return ApplicationRejected(
                application_id=application.id,
                company_id=application.company_id,
                previous_status=current.value,
            )
        event_cls = _FORWARD_TRANSITION_EVENTS.get((current, target))
        if event_cls is None:
            return None
        return event_cls(application_id=application.id, company_id=application.company_id)

    @staticmethod
    def _validate_transition(current: ApplicationStatus, target: ApplicationStatus) -> None:
        allowed = _ALLOWED_TRANSITIONS.get(current, set())
        if target not in allowed:
            raise InvalidApplicationStatusTransitionError(
                f"Cannot transition an application from '{current.value}' to '{target.value}'."
            )

    @staticmethod
    def _assert_job_is_open(job_status: str) -> None:
        if job_status != JobStatus.OPEN.value:
            raise JobNotOpenForApplicationsError(
                "This job is not currently accepting applications."
            )

    @staticmethod
    def _assert_valid_candidate(user: User) -> None:
        # Defense in depth — RBAC (require_roles(Role.CANDIDATE)) already
        # restricts these endpoints, same reasoning as
        # JobService._assert_internal_with_company.
        if user.account_type != AccountType.CANDIDATE.value:
            raise InvalidCandidateError("Only candidate accounts can submit applications.")
