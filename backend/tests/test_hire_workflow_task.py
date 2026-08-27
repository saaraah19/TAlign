"""
Tests for HireWorkflowRunner (app/workflow_engine/tasks.py) — the
orchestration layer that fetches the Application, builds
HireWorkflowContext, runs HireCandidateWorkflow through WorkflowEngine,
and persists the resulting WorkflowRun. All repositories/services are
mocked — no live database, same approach as every other service test
in this suite.
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock

from app.models.application import Application, ApplicationStatus
from app.models.company import Company
from app.models.email import Email, EmailStatus
from app.models.employee import Employee
from app.models.job import Job
from app.models.onboarding_task import OnboardingTask
from app.models.user import User
from app.models.workflow_run import WorkflowRunStatus
from app.workflow_engine.engine import WorkflowEngine
from app.workflow_engine.tasks import HireWorkflowRunner


def _make_application(
    *, company_id: uuid.UUID, status: str = ApplicationStatus.HIRED.value
) -> Application:
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
        status=status,
        updated_at=datetime(2026, 8, 20, tzinfo=timezone.utc),
    )
    application.candidate = candidate
    application.job = job
    return application


def _make_company(company_id: uuid.UUID) -> Company:
    return Company(id=company_id, name="Talign", slug="talign")


def _make_runner(
    *,
    application: Application | None,
    company: Company | None,
    employee_created: bool = True,
    onboarding_created: bool = True,
    email_created: bool = True,
):
    application_repo = AsyncMock()
    application_repo.get_by_id_with_relations.return_value = application

    company_repo = AsyncMock()
    company_repo.get_by_id.return_value = company

    workflow_run_repo = AsyncMock()
    workflow_run_repo.create.side_effect = lambda run: run

    employee_service = AsyncMock()
    if application is not None:
        employee = Employee(
            id=uuid.uuid4(),
            company_id=application.company_id,
            application_id=application.id,
            first_name="Ahmed",
            last_name="Benali",
            email="ahmed@example.com",
            job_title="Backend Engineer",
            hire_date=datetime(2026, 8, 20).date(),
        )
        employee_service.create_employee.return_value = (employee, employee_created)
        employee_service.create_onboarding_checklist.return_value = (
            [OnboardingTask(id=uuid.uuid4(), employee_id=employee.id, title="Set up workstation")],
            onboarding_created,
        )

    communication_service = AsyncMock()
    if application is not None:
        email = Email(
            id=uuid.uuid4(),
            application_id=application.id,
            company_id=application.company_id,
            email_type="onboarding_welcome",
            status=EmailStatus.DRAFT.value,
            recipient_email="ahmed@example.com",
            subject="Welcome!",
            body="Congrats.",
        )
        communication_service.generate_system_draft.return_value = (email, email_created)

    db = AsyncMock()

    runner = HireWorkflowRunner(
        db,
        application_repository=application_repo,
        company_repository=company_repo,
        workflow_run_repository=workflow_run_repo,
        employee_service=employee_service,
        communication_service=communication_service,
        engine=WorkflowEngine(),
    )
    return runner, db, workflow_run_repo, employee_service, communication_service


# --- successful complete run ---


async def test_successful_run_persists_a_success_workflow_run() -> None:
    company_id = uuid.uuid4()
    application = _make_application(company_id=company_id)
    company = _make_company(company_id)
    runner, db, workflow_run_repo, _, _ = _make_runner(application=application, company=company)

    run = await runner.run(application.id)

    assert run is not None
    assert run.status == WorkflowRunStatus.SUCCESS.value
    assert run.trigger_entity_type == "application"
    assert run.trigger_entity_id == application.id
    assert run.company_id == company_id
    assert run.completed_steps == [
        "create_employee_record",
        "create_onboarding_checklist",
        "draft_welcome_email",
    ]
    assert run.failed_step is None
    workflow_run_repo.create.assert_awaited_once()
    db.commit.assert_awaited_once()


# --- duplicate trigger / idempotency ---


async def test_duplicate_trigger_persists_a_skipped_workflow_run() -> None:
    """
    The core idempotency-observability requirement: triggering the hire
    workflow a second time for an Application that's already fully
    processed (every step's service call reports created=False) must
    record SKIPPED, not SUCCESS — so a duplicate trigger is visible in
    the audit trail rather than indistinguishable from fresh work.
    """
    company_id = uuid.uuid4()
    application = _make_application(company_id=company_id)
    company = _make_company(company_id)
    runner, _, workflow_run_repo, employee_service, communication_service = _make_runner(
        application=application,
        company=company,
        employee_created=False,
        onboarding_created=False,
        email_created=False,
    )

    run = await runner.run(application.id)

    assert run is not None
    assert run.status == WorkflowRunStatus.SKIPPED.value
    # The steps still "ran" (idempotency was checked), just did no new work.
    assert run.completed_steps == [
        "create_employee_record",
        "create_onboarding_checklist",
        "draft_welcome_email",
    ]
    employee_service.create_employee.assert_awaited_once()
    communication_service.generate_system_draft.assert_awaited_once()


async def test_partial_duplicate_trigger_is_still_recorded_as_success() -> None:
    """
    If only SOME steps had already run (e.g. a prior partial failure
    left the employee created but no onboarding checklist yet), this
    trigger does real new work and must be SUCCESS, not SKIPPED —
    SKIPPED means "nothing at all happened," not "something happened
    once before."
    """
    company_id = uuid.uuid4()
    application = _make_application(company_id=company_id)
    company = _make_company(company_id)
    runner, *_rest = _make_runner(
        application=application,
        company=company,
        employee_created=False,  # already existed from a prior run
        onboarding_created=True,  # new this time
        email_created=True,
    )

    run = await runner.run(application.id)

    assert run.status == WorkflowRunStatus.SUCCESS.value


# --- failure persistence ---


async def test_failure_in_a_step_persists_a_failed_workflow_run_with_failed_step() -> None:
    company_id = uuid.uuid4()
    application = _make_application(company_id=company_id)
    company = _make_company(company_id)
    runner, _, workflow_run_repo, employee_service, communication_service = _make_runner(
        application=application, company=company
    )
    communication_service.generate_system_draft.side_effect = RuntimeError("LLM unavailable")

    run = await runner.run(application.id)

    assert run is not None
    assert run.status == WorkflowRunStatus.FAILED.value
    assert run.failed_step == "draft_welcome_email"
    assert run.completed_steps == ["create_employee_record", "create_onboarding_checklist"]
    assert "LLM unavailable" in run.error


# --- cross-company isolation ---


async def test_workflow_run_is_scoped_to_the_applications_own_company() -> None:
    """
    The persisted WorkflowRun's company_id must always match the
    triggering Application's own company_id — never anything else, e.g.
    an acting user's company or a default. This is the load-bearing
    field for any future Dashboard query that lists "workflow runs for
    my company," so a wrong value here would be a cross-tenant leak in
    the audit log itself.
    """
    company_a = uuid.uuid4()
    company_b = uuid.uuid4()
    application = _make_application(company_id=company_a)
    company = _make_company(company_a)
    runner, *_rest = _make_runner(application=application, company=company)

    run = await runner.run(application.id)

    assert run.company_id == company_a
    assert run.company_id != company_b


async def test_employee_created_for_the_applications_company_not_any_other() -> None:
    """
    Complements the above at the EmployeeService boundary: the context
    built from the Application must carry that Application's own
    company_id through to EmployeeService, never a different one.
    """
    company_id = uuid.uuid4()
    application = _make_application(company_id=company_id)
    company = _make_company(company_id)
    runner, _, _, employee_service, _ = _make_runner(application=application, company=company)

    await runner.run(application.id)

    context_arg = employee_service.create_employee.call_args[0][0]
    assert context_arg.company_id == company_id


# --- guard clauses ---


async def test_application_not_found_returns_none_and_does_not_persist_a_run() -> None:
    runner, db, workflow_run_repo, _, _ = _make_runner(application=None, company=None)

    run = await runner.run(uuid.uuid4())

    assert run is None
    workflow_run_repo.create.assert_not_awaited()
    db.commit.assert_not_awaited()


async def test_application_not_hired_returns_none_and_does_not_persist_a_run() -> None:
    company_id = uuid.uuid4()
    application = _make_application(company_id=company_id, status=ApplicationStatus.OFFER.value)
    company = _make_company(company_id)
    runner, db, workflow_run_repo, _, _ = _make_runner(application=application, company=company)

    run = await runner.run(application.id)

    assert run is None
    workflow_run_repo.create.assert_not_awaited()
    db.commit.assert_not_awaited()


# --- never auto-sends ---


async def test_full_run_never_calls_mark_as_sent() -> None:
    company_id = uuid.uuid4()
    application = _make_application(company_id=company_id)
    company = _make_company(company_id)
    runner, _, _, _, communication_service = _make_runner(application=application, company=company)

    await runner.run(application.id)

    communication_service.mark_as_sent.assert_not_called()
