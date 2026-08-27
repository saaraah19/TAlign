"""
EmployeeService.

Owns exactly two things, both called by HireCandidateWorkflow and
nothing else: creating the thin Employee record, and creating its
starter onboarding checklist. No Workflow Engine, no Compass, no
Agent, no LLM call anywhere in this file — this is plain deterministic
persistence, matching CLAUDE.md's principle that business logic
belongs to domain services, not to the Workflow Engine itself.

Both methods are idempotent, independently of each other, and return
`(result, created: bool)` so callers (the workflow, and WorkflowRun
bookkeeping) can distinguish "did real work" from "already existed,
did nothing" — this is the service-layer half of Slice 7's idempotency
requirement. `Employee.application_id` being UNIQUE at the DB layer is
the second layer of that same guarantee (see app/models/employee.py).
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.employee import Employee
from app.models.onboarding_task import OnboardingTask
from app.repositories.employee_repository import EmployeeRepository
from app.repositories.onboarding_task_repository import OnboardingTaskRepository
from app.workflow_engine.context import HireWorkflowContext

#: Deliberately fixed and unconfigurable for the MVP — see
#: app/models/onboarding_task.py's module docstring. A templating
#: system (per-role checklists, admin-editable templates) is real
#: Product Book territory but explicitly V2.
DEFAULT_ONBOARDING_TASKS: tuple[str, ...] = (
    "Set up workstation",
    "IT account provisioning",
    "Manager intro meeting",
    "Complete new-hire paperwork",
)


class EmployeeService:
    def __init__(
        self,
        db: AsyncSession,
        employee_repository: EmployeeRepository | None = None,
        onboarding_task_repository: OnboardingTaskRepository | None = None,
    ) -> None:
        self._db = db
        self._employees = employee_repository or EmployeeRepository(db)
        self._onboarding_tasks = onboarding_task_repository or OnboardingTaskRepository(db)

    async def create_employee(self, context: HireWorkflowContext) -> tuple[Employee, bool]:
        """Returns (employee, created). `created=False` means a hire workflow
        already ran for this application and the existing row was returned."""
        existing = await self._employees.get_by_application_id(context.application_id)
        if existing is not None:
            return existing, False

        employee = Employee(
            company_id=context.company_id,
            application_id=context.application_id,
            first_name=context.candidate_first_name,
            last_name=context.candidate_last_name,
            email=context.candidate_email,
            job_title=context.job_title,
            hire_date=context.hire_date,
        )
        persisted = await self._employees.create(employee)
        await self._db.commit()
        return persisted, True

    async def create_onboarding_checklist(
        self, employee_id: uuid.UUID
    ) -> tuple[list[OnboardingTask], bool]:
        """Returns (tasks, created). `created=False` means a checklist already
        existed for this employee and nothing new was inserted."""
        existing = await self._onboarding_tasks.list_for_employee(employee_id)
        if existing:
            return existing, False

        tasks = [
            OnboardingTask(employee_id=employee_id, title=title)
            for title in DEFAULT_ONBOARDING_TASKS
        ]
        persisted = await self._onboarding_tasks.create_many(tasks)
        await self._db.commit()
        return persisted, True
