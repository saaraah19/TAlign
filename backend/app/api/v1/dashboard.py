"""
Dashboard endpoint.

One read, `GET /dashboard`. RBAC-scoped to ADMIN/RECRUITER/HIRING_MANAGER
-- the same three internal roles already used for pipeline reads
throughout this codebase (_PIPELINE_READ_ROLES in applications.py) --
CANDIDATE and EMPLOYEE have no business seeing another user's recruiter
workload.

No POST/PUT/DELETE here -- the Dashboard is entirely a read
composition over data mutated elsewhere (Applications, Jobs, Emails,
ResumeAnalysis, WorkflowRun). The one piece of state this endpoint can
cause to be written -- the cached DashboardBrief row -- happens as a
side effect of DashboardService.get_dashboard() the first time it's
called for a given company on a given day, not via a dedicated write
route.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.core.roles import Role
from app.database.session import get_db
from app.models.user import User
from app.schemas.application import ApplicationWithCandidate
from app.schemas.dashboard import (
    DashboardBriefRead,
    DashboardRead,
    LowApplicantJobRead,
    RecentAnalysisRead,
)
from app.schemas.email import EmailRead
from app.schemas.employee import WorkflowRunRead
from app.services.dashboard_service import DashboardService

router = APIRouter()

_DASHBOARD_READ_ROLES = (Role.ADMIN, Role.RECRUITER, Role.HIRING_MANAGER)


@router.get("", response_model=DashboardRead)
async def get_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*_DASHBOARD_READ_ROLES)),
) -> DashboardRead:
    data = await DashboardService(db).get_dashboard(current_user)

    return DashboardRead(
        brief=(DashboardBriefRead.model_validate(data.brief) if data.brief else None),
        awaiting_review=[
            ApplicationWithCandidate.model_validate(a) for a in data.awaiting_review
        ],
        low_applicant_jobs=[
            LowApplicantJobRead(job_id=job.id, title=job.title, applicant_count=count)
            for job, count in data.low_applicant_jobs
        ],
        recent_analyses=[
            RecentAnalysisRead(
                analysis_id=analysis.id,
                application_id=analysis.application_id,
                candidate_name=(
                    f"{analysis.application.candidate.first_name} "
                    f"{analysis.application.candidate.last_name}"
                ),
                job_title=analysis.application.job.title,
                overall_score=analysis.overall_score,
                analyzed_at=analysis.analyzed_at,
            )
            for analysis in data.recent_analyses
        ],
        recent_workflow_runs=[
            WorkflowRunRead.model_validate(run) for run in data.recent_workflow_runs
        ],
        pending_drafts=[EmailRead.model_validate(email) for email in data.pending_drafts],
    )
