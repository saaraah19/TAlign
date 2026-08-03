"""
Tests for CommunicationService: idempotent drafting, the DRAFT/SENT
lifecycle guard, and application-not-found handling. Same mocked-
repository approach as tests/test_application_service_rules.py — no
live database, no pytest-asyncio fixtures beyond plain async functions.
"""

import uuid
from unittest.mock import AsyncMock

import pytest

from app.agents.communication.agent import DraftOutcome
from app.agents.communication.schemas import DraftEmailSchema
from app.core.exceptions import EmailAlreadySentError, NotFoundError
from app.models.application import Application
from app.models.company import Company
from app.models.email import Email, EmailStatus
from app.models.job import Job
from app.models.user import User
from app.services.communication_service import CommunicationService

_SAMPLE_OUTCOME = DraftOutcome(
    schema=DraftEmailSchema(subject="Update on your application", body="Thanks for applying."),
    llm_provider="fakellm",
    llm_model="fake-model",
    prompt_version="rejection_email_v1",
)


def _make_application(company_id: uuid.UUID) -> Application:
    candidate = User(
        id=uuid.uuid4(),
        company_id=None,
        account_type="candidate",
        email="ahmed@example.com",
        password_hash="x",
        first_name="Ahmed",
        last_name="Benali",
    )
    job = Job(
        id=uuid.uuid4(),
        company_id=company_id,
        title="Backend Engineer",
        description="...",
        employment_type="full_time",
    )
    application = Application(
        id=uuid.uuid4(),
        candidate_id=candidate.id,
        job_id=job.id,
        company_id=company_id,
        status="applied",
    )
    application.candidate = candidate
    application.job = job
    return application


def _make_recruiter(company_id: uuid.UUID) -> User:
    return User(
        id=uuid.uuid4(),
        company_id=company_id,
        account_type="internal",
        email="emma@example.com",
        password_hash="x",
        first_name="Emma",
        last_name="Martin",
    )


def _make_service(*, application: Application | None, existing_draft: Email | None = None):
    application_repo = AsyncMock()
    application_repo.get_by_id_for_company.return_value = application

    email_repo = AsyncMock()
    email_repo.get_current_draft.return_value = existing_draft
    email_repo.create.side_effect = lambda e: e

    company_repo = AsyncMock()
    company_repo.get_by_id.return_value = (
        Company(id=application.company_id, name="Talign", slug="talign") if application else None
    )

    analysis_repo = AsyncMock()
    analysis_repo.get_latest_completed_for_application.return_value = None

    agent = AsyncMock()
    agent.draft_rejection.return_value = _SAMPLE_OUTCOME
    agent.draft_interview_invitation.return_value = _SAMPLE_OUTCOME

    db = AsyncMock()

    service = CommunicationService(
        db,
        email_repository=email_repo,
        application_repository=application_repo,
        company_repository=company_repo,
        resume_analysis_repository=analysis_repo,
        agent=agent,
    )
    return service, email_repo, agent


async def test_generate_draft_creates_new_email_when_none_exists() -> None:
    company_id = uuid.uuid4()
    application = _make_application(company_id)
    recruiter = _make_recruiter(company_id)
    service, email_repo, agent = _make_service(application=application, existing_draft=None)

    email = await service.generate_draft(
        application_id=application.id, email_type="rejection", acting_user=recruiter
    )

    assert email.subject == _SAMPLE_OUTCOME.schema.subject
    assert email.recipient_email == "ahmed@example.com"
    agent.draft_rejection.assert_called_once()
    email_repo.create.assert_called_once()


async def test_generate_draft_is_idempotent_and_skips_the_llm_call() -> None:
    company_id = uuid.uuid4()
    application = _make_application(company_id)
    recruiter = _make_recruiter(company_id)
    existing = Email(
        id=uuid.uuid4(),
        application_id=application.id,
        company_id=company_id,
        email_type="rejection",
        status=EmailStatus.DRAFT.value,
        recipient_email="ahmed@example.com",
        subject="Existing draft",
        body="Already drafted.",
    )
    service, email_repo, agent = _make_service(application=application, existing_draft=existing)

    email = await service.generate_draft(
        application_id=application.id, email_type="rejection", acting_user=recruiter
    )

    assert email is existing
    agent.draft_rejection.assert_not_called()
    email_repo.create.assert_not_called()


async def test_generate_draft_raises_not_found_for_unknown_application() -> None:
    company_id = uuid.uuid4()
    recruiter = _make_recruiter(company_id)
    service, _, agent = _make_service(application=None)

    with pytest.raises(NotFoundError):
        await service.generate_draft(
            application_id=uuid.uuid4(), email_type="rejection", acting_user=recruiter
        )

    agent.draft_rejection.assert_not_called()


async def test_cannot_edit_an_already_sent_email() -> None:
    company_id = uuid.uuid4()
    application = _make_application(company_id)
    recruiter = _make_recruiter(company_id)
    sent_email = Email(
        id=uuid.uuid4(),
        application_id=application.id,
        company_id=company_id,
        email_type="rejection",
        status=EmailStatus.SENT.value,
        recipient_email="ahmed@example.com",
        subject="Already sent",
        body="This was sent already.",
    )
    service, email_repo, _ = _make_service(application=application)
    email_repo.get_by_id_for_company.return_value = sent_email

    with pytest.raises(EmailAlreadySentError):
        await service.update_draft(
            email_id=sent_email.id, subject="New subject", body="New body", acting_user=recruiter
        )


async def test_cannot_send_an_already_sent_email() -> None:
    company_id = uuid.uuid4()
    application = _make_application(company_id)
    recruiter = _make_recruiter(company_id)
    sent_email = Email(
        id=uuid.uuid4(),
        application_id=application.id,
        company_id=company_id,
        email_type="rejection",
        status=EmailStatus.SENT.value,
        recipient_email="ahmed@example.com",
        subject="Already sent",
        body="This was sent already.",
    )
    service, email_repo, _ = _make_service(application=application)
    email_repo.get_by_id_for_company.return_value = sent_email

    with pytest.raises(EmailAlreadySentError):
        await service.mark_as_sent(email_id=sent_email.id, acting_user=recruiter)


async def test_cannot_regenerate_an_already_sent_email() -> None:
    company_id = uuid.uuid4()
    application = _make_application(company_id)
    recruiter = _make_recruiter(company_id)
    sent_email = Email(
        id=uuid.uuid4(),
        application_id=application.id,
        company_id=company_id,
        email_type="rejection",
        status=EmailStatus.SENT.value,
        recipient_email="ahmed@example.com",
        subject="Already sent",
        body="This was sent already.",
    )
    service, email_repo, agent = _make_service(application=application)
    email_repo.get_by_id_for_company.return_value = sent_email

    with pytest.raises(EmailAlreadySentError):
        await service.regenerate_draft(email_id=sent_email.id, acting_user=recruiter)

    agent.draft_rejection.assert_not_called()
