"""
HireCandidateWorkflow.

The first real Workflow in this codebase. Runs when an Application
transitions OFFER -> HIRED (triggered from
app/api/v1/applications.py's transition endpoint via
app/workflow_engine/tasks.py's run_hire_workflow_task — see that
module for the trigger mechanism and WorkflowRun persistence).

Three deterministic steps, in order:
  1. create_employee_record    -> EmployeeService.create_employee
  2. create_onboarding_checklist -> EmployeeService.create_onboarding_checklist
  3. draft_welcome_email       -> CommunicationService.generate_system_draft

No LLM reasoning happens in this file. Step 3 delegates entirely to
CommunicationService (which delegates to CommunicationAgent) — this
class only decides WHICH steps run and in WHAT order, never HOW the
email content gets generated. Same "Workflow Engine invokes agents but
never reasons itself" rule the Slice 7 scope description states
explicitly.

Idempotent as a whole because every step is independently idempotent
(see EmployeeService / CommunicationService docstrings): triggering
this workflow twice for the same Application never creates duplicate
Employee/OnboardingTask/Email rows. The second run's `state` reports
`created=False` for every step, which is what lets
run_hire_workflow_task tell a genuine duplicate trigger (SKIPPED) apart
from real work (SUCCESS).
"""

from typing import Any

from app.services.communication_service import CommunicationService
from app.services.employee_service import EmployeeService
from app.workflow_engine.context import HireWorkflowContext
from app.workflow_engine.workflow import Workflow, WorkflowStep


class HireCandidateWorkflow(Workflow):
    name = "hire_candidate"

    def __init__(
        self,
        context: HireWorkflowContext,
        employee_service: EmployeeService,
        communication_service: CommunicationService,
    ) -> None:
        self._context = context
        self._employees = employee_service
        self._communication = communication_service
        self.steps: list[WorkflowStep] = [
            WorkflowStep("create_employee_record", self._create_employee_record),
            WorkflowStep("create_onboarding_checklist", self._create_onboarding_checklist),
            WorkflowStep("draft_welcome_email", self._draft_welcome_email),
        ]

    async def _create_employee_record(self, state: dict[str, Any]) -> dict[str, Any]:
        employee, created = await self._employees.create_employee(self._context)
        return {"employee_id": employee.id, "employee_created": created}

    async def _create_onboarding_checklist(self, state: dict[str, Any]) -> dict[str, Any]:
        employee_id = state["employee_id"]
        tasks, created = await self._employees.create_onboarding_checklist(employee_id)
        return {
            "onboarding_task_ids": [task.id for task in tasks],
            "onboarding_created": created,
        }

    async def _draft_welcome_email(self, state: dict[str, Any]) -> dict[str, Any]:
        email, created = await self._communication.generate_system_draft(
            application_id=self._context.application_id,
            company_id=self._context.company_id,
            email_type="onboarding_welcome",
            recipient_email=self._context.candidate_email,
            candidate_first_name=self._context.candidate_first_name,
            job_title=self._context.job_title,
            company_name=self._context.company_name,
        )
        return {"welcome_email_id": email.id, "welcome_email_created": created}
