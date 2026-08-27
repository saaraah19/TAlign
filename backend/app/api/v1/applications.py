"""
Applications endpoints.

Two audiences, two sets of routes:
  - Candidate-facing: POST / (apply), GET /mine, GET /mine/{id}, PUT
    /mine/{id}/resume (Slice 4), GET /mine/{id}/analysis-status (Slice 4).
  - Recruiter-facing: GET / (pipeline), GET /{id}, POST /{id}/transition,
    GET /{id}/analysis (Slice 4), GET /{id}/analysis/history (Slice 4),
    GET /{id}/analysis-status (Slice 4), POST /{id}/reanalyze (Slice 4).

Route ORDER matters here: /mine and /mine/{application_id}(/...) are
registered before /{application_id} so FastAPI/Starlette matches the
literal "/mine" segment before it could be captured by the
"/{application_id}" path parameter pattern.

Slice 4 note on candidate-facing analysis exposure: the candidate status
endpoint returns ONLY `AnalysisProgressStatusRead` (a bare status enum) —
there is no candidate-accessible route anywhere in this file that could
return `ResumeAnalysisRead` (score/skills/strengths/concerns). That's not
a filter applied to a response; it's simply not wired to any route a
candidate's RBAC dependency would pass.
"""

import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.core.roles import Role
from app.database.session import get_db
from app.models.application import ApplicationStatus
from app.models.user import User
from app.schemas.application import (
    ApplicationCreateRequest,
    ApplicationListResponse,
    ApplicationStatusTransitionRequest,
    ApplicationWithCandidate,
    ApplicationWithJob,
    PipelineListResponse,
)
from app.schemas.resume_analysis import (
    AnalysisProgressStatusRead,
    AttachResumeRequest,
    ResumeAnalysisHistoryResponse,
    ResumeAnalysisRead,
)
from app.services.application_service import ApplicationService
from app.services.resume_analysis_service import ResumeAnalysisService, run_resume_analysis_task
from app.schemas.employee import HireWorkflowStatusRead
from app.workflow_engine.status import get_hire_workflow_status
from app.workflow_engine.tasks import run_hire_workflow_task

router = APIRouter()

_PIPELINE_READ_ROLES = (Role.ADMIN, Role.RECRUITER, Role.HIRING_MANAGER)
_PIPELINE_WRITE_ROLES = (Role.ADMIN, Role.RECRUITER)


# --- Candidate-facing ---


@router.post("", response_model=ApplicationWithJob, status_code=201)
async def apply_to_job(
    payload: ApplicationCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(Role.CANDIDATE)),
) -> ApplicationWithJob:
    application = await ApplicationService(db).apply(
        candidate=current_user, job_id=payload.job_id
    )
    # apply() doesn't eager-load `job` (it just built the Application from
    # a Job it already had in hand) — re-fetch through the candidate-
    # scoped read path so the response includes it, same as every other
    # create-then-return-with-relations endpoint in this codebase.
    full = await ApplicationService(db).get_my_application(
        application_id=application.id, candidate=current_user
    )
    return ApplicationWithJob.model_validate(full)


@router.get("/mine", response_model=ApplicationListResponse)
async def list_my_applications(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(Role.CANDIDATE)),
) -> ApplicationListResponse:
    applications, total = await ApplicationService(db).list_my_applications(
        candidate=current_user, page=page, page_size=page_size
    )
    return ApplicationListResponse(
        items=[ApplicationWithJob.model_validate(a) for a in applications],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/mine/{application_id}", response_model=ApplicationWithJob)
async def get_my_application(
    application_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(Role.CANDIDATE)),
) -> ApplicationWithJob:
    application = await ApplicationService(db).get_my_application(
        application_id=application_id, candidate=current_user
    )
    return ApplicationWithJob.model_validate(application)


@router.put("/mine/{application_id}/resume", response_model=ApplicationWithJob)
async def attach_resume_to_application(
    application_id: uuid.UUID,
    payload: AttachResumeRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(Role.CANDIDATE)),
) -> ApplicationWithJob:
    """
    Sets the application's current resume and schedules a fresh analysis
    run in the background — this call IS the "explicit user action" that
    authorizes a new analysis version (see ApplicationService.attach_resume's
    docstring). The response returns immediately; the candidate polls
    GET /mine/{id}/analysis-status to watch progress.
    """
    application = await ApplicationService(db).attach_resume(
        application_id=application_id, resume_id=payload.resume_id, candidate=current_user
    )
    background_tasks.add_task(run_resume_analysis_task, application.id)

    full = await ApplicationService(db).get_my_application(
        application_id=application.id, candidate=current_user
    )
    return ApplicationWithJob.model_validate(full)


@router.get("/mine/{application_id}/analysis-status", response_model=AnalysisProgressStatusRead)
async def get_my_analysis_status(
    application_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(Role.CANDIDATE)),
) -> AnalysisProgressStatusRead:
    """
    Candidate-facing progress polling. Returns ONLY a coarse status enum
    (uploading/parsing/analyzing/complete/failed as the frontend renders
    them) — never score, skills, or any other analysis content. See
    module docstring.
    """
    application = await ApplicationService(db).get_my_application(
        application_id=application_id, candidate=current_user
    )
    status = await ResumeAnalysisService(db).get_progress_status(application)
    return AnalysisProgressStatusRead(status=status)


# --- Recruiter-facing (company pipeline) ---


@router.get("", response_model=PipelineListResponse)
async def list_pipeline(
    job_id: uuid.UUID | None = Query(default=None),
    status: ApplicationStatus | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*_PIPELINE_READ_ROLES)),
) -> PipelineListResponse:
    applications, total = await ApplicationService(db).list_applications_for_company(
        acting_user=current_user,
        job_id=job_id,
        status=status.value if status else None,
        page=page,
        page_size=page_size,
    )
    return PipelineListResponse(
        items=[ApplicationWithCandidate.model_validate(a) for a in applications],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{application_id}", response_model=ApplicationWithCandidate)
async def get_application(
    application_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*_PIPELINE_READ_ROLES)),
) -> ApplicationWithCandidate:
    application = await ApplicationService(db).get_application_for_company(
        application_id=application_id, acting_user=current_user
    )
    return ApplicationWithCandidate.model_validate(application)


@router.post("/{application_id}/transition", response_model=ApplicationWithCandidate)
async def transition_application_status(
    application_id: uuid.UUID,
    payload: ApplicationStatusTransitionRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*_PIPELINE_WRITE_ROLES)),
) -> ApplicationWithCandidate:
    application, _event = await ApplicationService(db).transition_status(
        application_id=application_id,
        target_status=payload.target_status,
        acting_user=current_user,
    )
    if application.status == ApplicationStatus.HIRED.value:
        # Same pattern as attach_resume_to_application's resume-analysis
        # trigger above: direct BackgroundTasks scheduling, no event bus.
        # Slice 7's Workflow Engine — see
        # app/workflow_engine/tasks.py:run_hire_workflow_task.
        background_tasks.add_task(run_hire_workflow_task, application.id)
    # Re-fetch with relations for the response, same reasoning as apply().
    full = await ApplicationService(db).get_application_for_company(
        application_id=application.id, acting_user=current_user
    )
    return ApplicationWithCandidate.model_validate(full)


# --- Slice 7: Workflow Engine (hire workflow status, recruiter-facing) ---


@router.get("/{application_id}/hire-workflow", response_model=HireWorkflowStatusRead)
async def get_hire_workflow_status_endpoint(
    application_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*_PIPELINE_READ_ROLES)),
) -> HireWorkflowStatusRead:
    """
    Lets the frontend show whether HireCandidateWorkflow ran for this
    Application, its outcome (SUCCESS/FAILED/SKIPPED, completed steps,
    which one failed if any), and the Employee + onboarding checklist it
    created. Returns all-null/empty fields if the workflow hasn't run
    yet (e.g. the Application isn't HIRED, or the background task
    hasn't finished) rather than a 404 — "not run yet" is a normal,
    expected state here, not an error.
    """
    # get_application_for_company both scopes to the acting user's
    # company AND raises NotFoundError for a cross-company/nonexistent
    # id — this is what makes get_hire_workflow_status's internal
    # company_id assertion safe to rely on.
    application = await ApplicationService(db).get_application_for_company(
        application_id=application_id, acting_user=current_user
    )
    status = await get_hire_workflow_status(
        db, application_id=application_id, company_id=application.company_id
    )
    return HireWorkflowStatusRead.from_status(status)


@router.get("/{application_id}/analysis", response_model=ResumeAnalysisRead)
async def get_application_analysis(
    application_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*_PIPELINE_READ_ROLES)),
) -> ResumeAnalysisRead:
    """Latest COMPLETED analysis only — 404 if none exists yet (still processing, or none run)."""
    analysis = await ResumeAnalysisService(db).get_latest_completed_for_company(
        application_id=application_id, acting_user=current_user
    )
    return ResumeAnalysisRead.model_validate(analysis)


@router.get("/{application_id}/analysis/history", response_model=ResumeAnalysisHistoryResponse)
async def get_application_analysis_history(
    application_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*_PIPELINE_READ_ROLES)),
) -> ResumeAnalysisHistoryResponse:
    """Every analysis version for this application, newest first — internal HR use, per instruction."""
    history = await ResumeAnalysisService(db).list_history_for_company(
        application_id=application_id, acting_user=current_user
    )
    return ResumeAnalysisHistoryResponse(items=[ResumeAnalysisRead.model_validate(a) for a in history])


@router.get("/{application_id}/analysis-status", response_model=AnalysisProgressStatusRead)
async def get_application_analysis_status(
    application_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*_PIPELINE_READ_ROLES)),
) -> AnalysisProgressStatusRead:
    application = await ApplicationService(db).get_application_for_company(
        application_id=application_id, acting_user=current_user
    )
    status = await ResumeAnalysisService(db).get_progress_status(application)
    return AnalysisProgressStatusRead(status=status)


@router.post("/{application_id}/reanalyze", response_model=AnalysisProgressStatusRead, status_code=202)
async def reanalyze_application(
    application_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*_PIPELINE_WRITE_ROLES)),
) -> AnalysisProgressStatusRead:
    """
    Recruiter-triggered re-analysis using the application's CURRENT
    resume (doesn't change resume_id — pairs with an admin/recruiter
    having just edited the job's required_skills and wanting a fresh
    comparison). Always creates a new ResumeAnalysis version; never
    touches prior ones.
    """
    application = await ApplicationService(db).get_application_for_company(
        application_id=application_id, acting_user=current_user
    )
    background_tasks.add_task(run_resume_analysis_task, application.id)
    status = await ResumeAnalysisService(db).get_progress_status(application)
    return AnalysisProgressStatusRead(status=status)
