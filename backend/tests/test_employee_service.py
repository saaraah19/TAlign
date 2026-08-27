"""
Tests for EmployeeService: idempotent employee creation and onboarding
checklist creation. Same mocked-repository approach as
tests/test_communication_service_rules.py — no live database.
"""

import uuid
from datetime import date
from unittest.mock import AsyncMock

from app.models.employee import Employee
from app.models.onboarding_task import OnboardingTask
from app.services.employee_service import DEFAULT_ONBOARDING_TASKS, EmployeeService
from app.workflow_engine.context import HireWorkflowContext


def _make_context(**overrides: object) -> HireWorkflowContext:
    defaults: dict[str, object] = {
        "application_id": uuid.uuid4(),
        "company_id": uuid.uuid4(),
        "company_name": "Talign",
        "candidate_first_name": "Ahmed",
        "candidate_last_name": "Benali",
        "candidate_email": "ahmed@example.com",
        "job_title": "Backend Engineer",
        "hire_date": date(2026, 8, 20),
    }
    defaults.update(overrides)
    return HireWorkflowContext(**defaults)  # type: ignore[arg-type]


def _make_service(*, existing_employee: Employee | None = None, existing_tasks=None):
    employee_repo = AsyncMock()
    employee_repo.get_by_application_id.return_value = existing_employee
    employee_repo.create.side_effect = lambda e: e

    onboarding_repo = AsyncMock()
    onboarding_repo.list_for_employee.return_value = existing_tasks or []
    onboarding_repo.create_many.side_effect = lambda tasks: tasks

    db = AsyncMock()

    service = EmployeeService(
        db, employee_repository=employee_repo, onboarding_task_repository=onboarding_repo
    )
    return service, employee_repo, onboarding_repo


# --- create_employee ---


async def test_create_employee_creates_a_new_record_when_none_exists() -> None:
    context = _make_context()
    service, employee_repo, _ = _make_service(existing_employee=None)

    employee, created = await service.create_employee(context)

    assert created is True
    assert employee.first_name == "Ahmed"
    assert employee.company_id == context.company_id
    assert employee.application_id == context.application_id
    employee_repo.create.assert_called_once()


async def test_create_employee_is_idempotent_for_the_same_application() -> None:
    context = _make_context()
    existing = Employee(
        id=uuid.uuid4(),
        company_id=context.company_id,
        application_id=context.application_id,
        first_name="Ahmed",
        last_name="Benali",
        email="ahmed@example.com",
        job_title="Backend Engineer",
        hire_date=date(2026, 8, 20),
    )
    service, employee_repo, _ = _make_service(existing_employee=existing)

    employee, created = await service.create_employee(context)

    assert created is False
    assert employee is existing
    employee_repo.create.assert_not_called()


# --- create_onboarding_checklist ---


async def test_create_onboarding_checklist_creates_the_default_tasks() -> None:
    employee_id = uuid.uuid4()
    service, _, onboarding_repo = _make_service(existing_tasks=[])

    tasks, created = await service.create_onboarding_checklist(employee_id)

    assert created is True
    assert len(tasks) == len(DEFAULT_ONBOARDING_TASKS)
    assert {t.title for t in tasks} == set(DEFAULT_ONBOARDING_TASKS)
    assert all(t.employee_id == employee_id for t in tasks)
    onboarding_repo.create_many.assert_called_once()


async def test_create_onboarding_checklist_is_idempotent_for_the_same_employee() -> None:
    employee_id = uuid.uuid4()
    existing = [OnboardingTask(id=uuid.uuid4(), employee_id=employee_id, title="Already there")]
    service, _, onboarding_repo = _make_service(existing_tasks=existing)

    tasks, created = await service.create_onboarding_checklist(employee_id)

    assert created is False
    assert tasks == existing
    onboarding_repo.create_many.assert_not_called()
