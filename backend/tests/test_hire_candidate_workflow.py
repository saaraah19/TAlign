"""
Tests for HireCandidateWorkflow — the concrete three-step workflow,
run through the real WorkflowEngine but with EmployeeService and
CommunicationService mocked (no DB, no LLM). Complements
test_workflow_engine.py (generic engine mechanics) and
test_employee_service.py / test_communication_service_rules.py
(the services' own business rules).
"""

import uuid
from datetime import date
from unittest.mock import AsyncMock

from app.models.email import Email, EmailStatus
from app.models.employee import Employee
from app.models.onboarding_task import OnboardingTask
from app.workflow_engine.context import HireWorkflowContext
from app.workflow_engine.engine import WorkflowEngine
from app.workflow_engine.workflows.hire_candidate import HireCandidateWorkflow


def _context() -> HireWorkflowContext:
    return HireWorkflowContext(
        application_id=uuid.uuid4(),
        company_id=uuid.uuid4(),
        company_name="Talign",
        candidate_first_name="Ahmed",
        candidate_last_name="Benali",
        candidate_email="ahmed@example.com",
        job_title="Backend Engineer",
        hire_date=date(2026, 8, 20),
    )


def _fresh_employee(context: HireWorkflowContext) -> Employee:
    return Employee(
        id=uuid.uuid4(),
        company_id=context.company_id,
        application_id=context.application_id,
        first_name=context.candidate_first_name,
        last_name=context.candidate_last_name,
        email=context.candidate_email,
        job_title=context.job_title,
        hire_date=context.hire_date,
    )


def _fresh_email(context: HireWorkflowContext) -> Email:
    return Email(
        id=uuid.uuid4(),
        application_id=context.application_id,
        company_id=context.company_id,
        email_type="onboarding_welcome",
        status=EmailStatus.DRAFT.value,
        recipient_email=context.candidate_email,
        subject="Welcome to the team!",
        body="Congratulations and welcome.",
    )


def _make_workflow(
    context: HireWorkflowContext,
    *,
    employee_created: bool = True,
    onboarding_created: bool = True,
    email_created: bool = True,
) -> tuple[HireCandidateWorkflow, AsyncMock, AsyncMock]:
    employee = _fresh_employee(context)
    email = _fresh_email(context)

    employee_service = AsyncMock()
    employee_service.create_employee.return_value = (employee, employee_created)
    employee_service.create_onboarding_checklist.return_value = (
        [OnboardingTask(id=uuid.uuid4(), employee_id=employee.id, title="Set up workstation")],
        onboarding_created,
    )

    communication_service = AsyncMock()
    communication_service.generate_system_draft.return_value = (email, email_created)

    workflow = HireCandidateWorkflow(
        context=context,
        employee_service=employee_service,
        communication_service=communication_service,
    )
    return workflow, employee_service, communication_service


# --- full successful run ---


async def test_successful_complete_workflow_runs_all_three_steps_in_order() -> None:
    context = _context()
    workflow, employee_service, communication_service = _make_workflow(context)

    result = await WorkflowEngine().run(workflow)

    assert result.success is True
    assert result.completed_steps == [
        "create_employee_record",
        "create_onboarding_checklist",
        "draft_welcome_email",
    ]
    assert result.output["employee_created"] is True
    assert result.output["onboarding_created"] is True
    assert result.output["welcome_email_created"] is True

    employee_service.create_employee.assert_awaited_once_with(context)
    employee_service.create_onboarding_checklist.assert_awaited_once()
    communication_service.generate_system_draft.assert_awaited_once()


async def test_email_step_receives_structured_context_fields_not_orm_objects() -> None:
    """
    Adjustment #2: the Communication Agent/Service boundary must only
    ever receive plain structured fields extracted from
    HireWorkflowContext, never the context object's own containers or
    any DB model.
    """
    context = _context()
    workflow, _, communication_service = _make_workflow(context)

    await WorkflowEngine().run(workflow)

    _, kwargs = communication_service.generate_system_draft.call_args
    assert kwargs["application_id"] == context.application_id
    assert kwargs["company_id"] == context.company_id
    assert kwargs["candidate_first_name"] == context.candidate_first_name
    assert kwargs["job_title"] == context.job_title
    assert kwargs["company_name"] == context.company_name
    assert kwargs["email_type"] == "onboarding_welcome"
    assert all(isinstance(v, (str, uuid.UUID)) for v in kwargs.values())


# --- failure at each individual step ---


async def test_failure_creating_employee_stops_before_onboarding_or_email() -> None:
    context = _context()
    workflow, employee_service, communication_service = _make_workflow(context)
    employee_service.create_employee.side_effect = RuntimeError("db unavailable")

    result = await WorkflowEngine().run(workflow)

    assert result.success is False
    assert result.failed_step == "create_employee_record"
    assert result.completed_steps == []
    employee_service.create_onboarding_checklist.assert_not_awaited()
    communication_service.generate_system_draft.assert_not_awaited()


async def test_failure_creating_onboarding_checklist_stops_before_email() -> None:
    context = _context()
    workflow, employee_service, communication_service = _make_workflow(context)
    employee_service.create_onboarding_checklist.side_effect = RuntimeError("constraint violation")

    result = await WorkflowEngine().run(workflow)

    assert result.success is False
    assert result.failed_step == "create_onboarding_checklist"
    assert result.completed_steps == ["create_employee_record"]
    communication_service.generate_system_draft.assert_not_awaited()


async def test_failure_drafting_welcome_email_still_leaves_employee_and_onboarding_done() -> None:
    """
    Partial completion: the LLM call failing must not roll back or hide
    the fact that the employee record and onboarding checklist DID get
    created — those are separate commits (see EmployeeService), and the
    WorkflowRun this feeds into must be able to show that.
    """
    context = _context()
    workflow, employee_service, communication_service = _make_workflow(context)
    communication_service.generate_system_draft.side_effect = RuntimeError(
        "LLM provider error"
    )

    result = await WorkflowEngine().run(workflow)

    assert result.success is False
    assert result.failed_step == "draft_welcome_email"
    assert result.completed_steps == ["create_employee_record", "create_onboarding_checklist"]
    employee_service.create_employee.assert_awaited_once()
    employee_service.create_onboarding_checklist.assert_awaited_once()


# --- duplicate trigger / idempotency, observed at the workflow level ---


async def test_duplicate_trigger_reports_created_false_for_every_step() -> None:
    """
    When every underlying service call is idempotent-and-already-done
    (as it would be on a second trigger for the same Application), the
    workflow still runs successfully to completion — it just does no new
    work. This is what run_hire_workflow_task uses to classify the
    overall WorkflowRun as SKIPPED rather than SUCCESS.
    """
    context = _context()
    workflow, _, _ = _make_workflow(
        context, employee_created=False, onboarding_created=False, email_created=False
    )

    result = await WorkflowEngine().run(workflow)

    assert result.success is True
    assert result.output["employee_created"] is False
    assert result.output["onboarding_created"] is False
    assert result.output["welcome_email_created"] is False


# --- draft-only, never auto-sends ---


async def test_workflow_only_creates_a_draft_email_never_marks_it_sent() -> None:
    """
    AI safety property: the workflow's only interaction with
    CommunicationService is generate_system_draft — it must never call
    mark_as_sent, regenerate_draft, or anything else that would move an
    email past DRAFT status automatically.
    """
    context = _context()
    workflow, _, communication_service = _make_workflow(context)

    await WorkflowEngine().run(workflow)

    communication_service.mark_as_sent.assert_not_called()
    communication_service.generate_system_draft.assert_awaited_once()
    # Only one CommunicationService method was ever touched.
    called_method_names = {
        call[0] for call in communication_service.method_calls if call[0] != "()"
    }
    assert called_method_names == {"generate_system_draft"}
