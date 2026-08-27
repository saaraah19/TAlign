"""
Workflow Engine task entrypoints.

FastAPI BackgroundTasks entrypoints, one per workflow the API layer can
trigger. Follows the exact precedent already established by
`run_resume_analysis_task` in resume_analysis_service.py: opens its own
database session (a background task runs after the triggering
request's session has already closed, so it cannot reuse
`Depends(get_db)`'s session), builds whatever input the workflow needs,
runs it through `WorkflowEngine`, and never lets an exception escape
past this boundary.

This is also where `WorkflowRun` persistence happens — deliberately
NOT inside `WorkflowEngine` (which stays DB-agnostic, pure sequencing)
and NOT inside `HireCandidateWorkflow` (which stays focused on business
steps). Deciding SUCCESS vs FAILED vs SKIPPED (see
app/models/workflow_run.py) is a call only this orchestration layer can
make, since it's the only place that sees every step's `created` flag
after the engine returns.

SKIPPED vs SUCCESS: if every step's `created` flag came back False
(every row already existed), the whole run is recorded as SKIPPED —
this is what makes a duplicate trigger of the same hire observable
rather than silently indistinguishable from a fresh run that happened
to do real work.
"""

import uuid

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application import Application, ApplicationStatus
from app.models.workflow_run import WorkflowRun, WorkflowRunStatus
from app.repositories.application_repository import ApplicationRepository
from app.repositories.company_repository import CompanyRepository
from app.repositories.workflow_run_repository import WorkflowRunRepository
from app.services.communication_service import CommunicationService
from app.services.employee_service import EmployeeService
from app.workflow_engine.context import HireWorkflowContext
from app.workflow_engine.engine import WorkflowEngine
from app.workflow_engine.workflow import WorkflowRunResult
from app.workflow_engine.workflows.hire_candidate import HireCandidateWorkflow

logger = structlog.get_logger(__name__)

_CREATED_FLAG_KEYS = ("employee_created", "onboarding_created", "welcome_email_created")


class HireWorkflowRunner:
    """
    The actual orchestration logic, factored out of the bare
    `run_hire_workflow_task` function so it can be unit tested with
    mocked repositories/services — same "every constructor accepts
    optional injected dependencies, defaulting to real ones" convention
    used by every other service in this codebase (see
    PROJECT_STATUS.md's engineering-conventions section). The module-
    level `run_hire_workflow_task` function below is the thin
    BackgroundTasks entrypoint that owns session lifecycle; this class
    owns the actual decision logic and is what tests exercise directly.
    """

    def __init__(
        self,
        db: AsyncSession,
        application_repository: ApplicationRepository | None = None,
        company_repository: CompanyRepository | None = None,
        workflow_run_repository: WorkflowRunRepository | None = None,
        employee_service: EmployeeService | None = None,
        communication_service: CommunicationService | None = None,
        engine: WorkflowEngine | None = None,
    ) -> None:
        self._db = db
        self._applications = application_repository or ApplicationRepository(db)
        self._companies = company_repository or CompanyRepository(db)
        self._workflow_runs = workflow_run_repository or WorkflowRunRepository(db)
        self._employee_service = employee_service or EmployeeService(db)
        self._communication_service = communication_service or CommunicationService(db)
        self._engine = engine or WorkflowEngine()

    async def run(self, application_id: uuid.UUID) -> WorkflowRun | None:
        """Returns the persisted WorkflowRun, or None if the guard clauses
        (application not found / not HIRED) short-circuited before any
        workflow ran — those cases are logged, not recorded as a run,
        since nothing was actually attempted against real data."""
        application = await self._applications.get_by_id_with_relations(application_id)
        if application is None:
            logger.warning(
                "hire_workflow_application_not_found", application_id=str(application_id)
            )
            return None

        if application.status != ApplicationStatus.HIRED.value:
            # Defensive guard: the endpoint only schedules this task on a
            # successful transition INTO hired, so this should never fire
            # in practice — but a background task should never trust that
            # its caller's precondition still holds by the time it
            # actually runs.
            logger.warning(
                "hire_workflow_application_not_hired",
                application_id=str(application_id),
                status=application.status,
            )
            return None

        company = await self._companies.get_by_id(application.company_id)
        assert company is not None  # FK guarantees this

        context = HireWorkflowContext(
            application_id=application.id,
            company_id=application.company_id,
            company_name=company.name,
            candidate_first_name=application.candidate.first_name,
            candidate_last_name=application.candidate.last_name,
            candidate_email=application.candidate.email,
            job_title=application.job.title,
            hire_date=application.updated_at.date(),
        )

        workflow = HireCandidateWorkflow(
            context=context,
            employee_service=self._employee_service,
            communication_service=self._communication_service,
        )
        result = await self._engine.run(workflow)

        run = _build_workflow_run(result, application, context)
        persisted = await self._workflow_runs.create(run)
        await self._db.commit()
        return persisted


async def run_hire_workflow_task(application_id: uuid.UUID) -> None:
    from app.database.session import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        try:
            await HireWorkflowRunner(db).run(application_id)
        except Exception:
            logger.exception("hire_workflow_task_failed", application_id=str(application_id))


def _build_workflow_run(
    result: WorkflowRunResult, application: Application, context: HireWorkflowContext
) -> WorkflowRun:
    if not result.success:
        status = WorkflowRunStatus.FAILED.value
    elif all(not result.output.get(key, True) for key in _CREATED_FLAG_KEYS):
        # Every step that actually ran reported created=False — nothing
        # new happened, this was a duplicate trigger. See module
        # docstring on why SKIPPED is tracked separately from SUCCESS.
        status = WorkflowRunStatus.SKIPPED.value
    else:
        status = WorkflowRunStatus.SUCCESS.value

    return WorkflowRun(
        company_id=context.company_id,
        workflow_name=result.workflow_name,
        trigger_entity_type="application",
        trigger_entity_id=application.id,
        status=status,
        completed_steps=result.completed_steps,
        failed_step=result.failed_step,
        error=result.error,
    )
