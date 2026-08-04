"""
CommunicationService.

Owns the Email lifecycle: generate a draft (calling CommunicationAgent),
let the recruiter regenerate or hand-edit it, and mark it sent. No
Workflow Engine, no Compass, no automatic triggering anywhere in this
file — every method here is invoked by an explicit recruiter action
(a button click), matching the "manual trigger only" scope decision for
this slice.

Re-fetch-after-commit note: every method that performs an UPDATE
(regenerate_draft, update_draft, mark_as_sent) re-fetches the row
before returning it. `Email.updated_at` is a server-side
`onupdate=func.now()` column, and touching it on an in-memory object
right after commit() — e.g. inside Pydantic's `model_validate` in the
API layer — raises `MissingGreenlet` (SQLAlchemy async attribute
expiration touched outside an awaited context). This exact bug was
diagnosed and fixed on Job's transition/update routes; centralizing the
re-fetch here means no caller of this service ever has to remember it.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.communication.agent import CommunicationAgent, DraftOutcome
from app.core.exceptions import AuthorizationError, EmailAlreadySentError, NotFoundError
from app.models.application import Application
from app.models.email import Email, EmailStatus
from app.models.user import User
from app.repositories.application_repository import ApplicationRepository
from app.repositories.company_repository import CompanyRepository
from app.repositories.email_repository import EmailRepository
from app.repositories.resume_analysis_repository import ResumeAnalysisRepository


class CommunicationService:
    def __init__(
        self,
        db: AsyncSession,
        email_repository: EmailRepository | None = None,
        application_repository: ApplicationRepository | None = None,
        company_repository: CompanyRepository | None = None,
        resume_analysis_repository: ResumeAnalysisRepository | None = None,
        agent: CommunicationAgent | None = None,
    ) -> None:
        self._db = db
        self._emails = email_repository or EmailRepository(db)
        self._applications = application_repository or ApplicationRepository(db)
        self._companies = company_repository or CompanyRepository(db)
        self._analyses = resume_analysis_repository or ResumeAnalysisRepository(db)
        self._agent = agent or CommunicationAgent()

    # --- Drafting ---

    async def generate_draft(
        self, *, application_id: uuid.UUID, email_type: str, acting_user: User
    ) -> Email:
        """
        Idempotent by design: if a draft of this type already exists
        for this application, it's returned as-is — no fresh LLM call,
        no duplicate row. Use `regenerate_draft` to force a fresh draft.
        """
        self._assert_internal_with_company(acting_user)
        application = await self._applications.get_by_id_for_company(
            application_id, acting_user.company_id
        )
        if application is None:
            raise NotFoundError("Application not found.")

        existing = await self._emails.get_current_draft(application_id, email_type)
        if existing is not None:
            return existing

        outcome = await self._generate_content(application, email_type)

        email = Email(
            application_id=application.id,
            company_id=application.company_id,
            created_by=acting_user.id,
            email_type=email_type,
            status=EmailStatus.DRAFT.value,
            recipient_email=application.candidate.email,
            subject=outcome.schema.subject,
            body=outcome.schema.body,
            llm_provider=outcome.llm_provider,
            llm_model=outcome.llm_model,
            prompt_version=outcome.prompt_version,
        )
        persisted = await self._emails.create(email)
        await self._db.commit()
        return persisted

    async def regenerate_draft(self, *, email_id: uuid.UUID, acting_user: User) -> Email:
        email = await self._get_owned_email(email_id, acting_user)
        self._assert_still_draft(email)

        application = await self._applications.get_by_id_for_company(
            email.application_id, acting_user.company_id
        )
        assert application is not None  # guaranteed by _get_owned_email's company scoping

        outcome = await self._generate_content(application, email.email_type)
        email.subject = outcome.schema.subject
        email.body = outcome.schema.body
        email.llm_provider = outcome.llm_provider
        email.llm_model = outcome.llm_model
        email.prompt_version = outcome.prompt_version
        await self._db.commit()

        return await self._reload(email.id)

    async def update_draft(
        self, *, email_id: uuid.UUID, subject: str, body: str, acting_user: User
    ) -> Email:
        """Manual recruiter edit — no LLM call."""
        email = await self._get_owned_email(email_id, acting_user)
        self._assert_still_draft(email)

        email.subject = subject
        email.body = body
        await self._db.commit()

        return await self._reload(email.id)

    async def mark_as_sent(self, *, email_id: uuid.UUID, acting_user: User) -> Email:
        email = await self._get_owned_email(email_id, acting_user)
        self._assert_still_draft(email)

        email.status = EmailStatus.SENT.value
        email.sent_at = datetime.now(UTC)
        await self._db.commit()

        return await self._reload(email.id)

    # --- Reads ---

    async def list_for_application(
        self, *, application_id: uuid.UUID, acting_user: User
    ) -> list[Email]:
        self._assert_internal_with_company(acting_user)
        application = await self._applications.get_by_id_for_company(
            application_id, acting_user.company_id
        )
        if application is None:
            raise NotFoundError("Application not found.")
        return await self._emails.list_for_application(application_id)

    # --- Internal helpers ---

    async def _generate_content(self, application: Application, email_type: str) -> DraftOutcome:
        company = await self._companies.get_by_id(application.company_id)
        assert company is not None  # FK guarantees this

        if email_type == "rejection":
            analysis = await self._analyses.get_latest_completed_for_application(application.id)
            strengths = analysis.strengths if analysis is not None else None
            return await self._agent.draft_rejection(
                candidate_first_name=application.candidate.first_name,
                job_title=application.job.title,
                company_name=company.name,
                strengths=strengths,
            )
        if email_type == "interview_invitation":
            return await self._agent.draft_interview_invitation(
                candidate_first_name=application.candidate.first_name,
                job_title=application.job.title,
                company_name=company.name,
            )
        raise ValueError(f"Unknown email_type: {email_type!r}")

    async def _get_owned_email(self, email_id: uuid.UUID, acting_user: User) -> Email:
        self._assert_internal_with_company(acting_user)
        email = await self._emails.get_by_id_for_company(email_id, acting_user.company_id)
        if email is None:
            raise NotFoundError("Email not found.")
        return email

    async def _reload(self, email_id: uuid.UUID) -> Email:
        """See module docstring — avoids returning an expired-attribute object post-commit."""
        reloaded = await self._emails.get_by_id(email_id)
        assert reloaded is not None
        return reloaded

    @staticmethod
    def _assert_still_draft(email: Email) -> None:
        if email.status != EmailStatus.DRAFT.value:
            raise EmailAlreadySentError(
                "This email has already been sent and can no longer be edited or regenerated."
            )

    @staticmethod
    def _assert_internal_with_company(user: User) -> None:
        # Same reasoning as JobService._assert_internal_with_company:
        # RBAC at the API layer already restricts every route in this
        # service to internal roles (ADMIN/RECRUITER), which always
        # carry a company_id — but a service should never trust that
        # its caller enforced its own preconditions correctly. This
        # also narrows `user.company_id` from `UUID | None` to `UUID`
        # for the type checker at every call site below.
        if user.company_id is None:
            raise AuthorizationError("This action requires an internal company account.")
