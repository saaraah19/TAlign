"""
Read-side query for hire-workflow status.

Backs the recruiter-facing GET /applications/{id}/hire-workflow
endpoint so the frontend can show whether Slice 7's
HireCandidateWorkflow ran for an Application, what it did
(SUCCESS/FAILED/SKIPPED, which steps completed, which one failed if
any), and its outputs — the created Employee and onboarding checklist.
The welcome-email draft itself is intentionally NOT duplicated here;
it's already reachable through the existing
GET /applications/{id}/emails endpoint (CommunicationPanel already
lists every email for an application, welcome included).

Deliberately a plain function, not a Service — it owns no business
rule or mutation, only composes three existing repositories' reads.
"""

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.employee import Employee
from app.models.onboarding_task import OnboardingTask
from app.models.workflow_run import WorkflowRun
from app.repositories.employee_repository import EmployeeRepository
from app.repositories.onboarding_task_repository import OnboardingTaskRepository
from app.repositories.workflow_run_repository import WorkflowRunRepository


@dataclass
class HireWorkflowStatus:
    workflow_run: WorkflowRun | None
    employee: Employee | None
    onboarding_tasks: list[OnboardingTask]


async def get_hire_workflow_status(
    db: AsyncSession, *, application_id: uuid.UUID, company_id: uuid.UUID
) -> HireWorkflowStatus:
    workflow_runs = WorkflowRunRepository(db)
    employees = EmployeeRepository(db)
    onboarding_tasks = OnboardingTaskRepository(db)

    run = await workflow_runs.get_latest_for_trigger("application", application_id)
    employee = await employees.get_by_application_id(application_id)
    tasks = await onboarding_tasks.list_for_employee(employee.id) if employee else []

    # Defensive assertion only — the caller (the API route) must already
    # have scoped `application_id` through ApplicationService's
    # company-checked read before calling this function. This is a
    # belt-and-suspenders check against a future caller skipping that.
    if employee is not None:
        assert employee.company_id == company_id

    return HireWorkflowStatus(workflow_run=run, employee=employee, onboarding_tasks=tasks)
