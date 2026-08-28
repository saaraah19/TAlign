"""
DashboardService.

Owns the entire Slice 8 read: five deterministic aggregation queries
(pending draft emails, applications awaiting review, low-applicant-
volume jobs, recently completed resume analyses, recent workflow runs)
plus one cached LLM-generated Daily Alignment Brief. No Compass, no
`agent_registry` -- see app/agents/dashboard/agent.py's module
docstring for why the Brief is generated here rather than through a
Compass chat turn.

The five deterministic lists are ALWAYS computed fresh on every call --
never cached, since they're cheap company-scoped queries and staleness
there would be actively misleading ("applications awaiting review"
showing yesterday's list is a real problem; a slightly-stale AI-written
paragraph is not). Only the Brief itself is cached, and only because it
involves an LLM call -- see app/models/dashboard_brief.py.

Graceful degradation is a deliberate design choice, not an oversight:
if the LLM call for the Brief fails (rate limit, timeout, bad schema
after retry), `get_dashboard` still returns everything else -- a
Dashboard with no Brief paragraph is still useful; a Dashboard that
500s because one LLM call failed is not.
"""

from datetime import UTC, datetime

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.dashboard.agent import DashboardAgent
from app.agents.dashboard.schemas import RecommendedAction
from app.core.exceptions import InvalidStructuredOutputError, LLMProviderError
from app.models.application import Application
from app.models.dashboard_brief import DashboardBrief
from app.models.email import Email
from app.models.job import Job
from app.models.resume_analysis import ResumeAnalysis
from app.models.user import User
from app.models.workflow_run import WorkflowRun
from app.repositories.application_repository import ApplicationRepository
from app.repositories.company_repository import CompanyRepository
from app.repositories.dashboard_brief_repository import DashboardBriefRepository
from app.repositories.email_repository import EmailRepository
from app.repositories.job_repository import JobRepository
from app.repositories.resume_analysis_repository import ResumeAnalysisRepository
from app.repositories.workflow_run_repository import WorkflowRunRepository

logger = structlog.get_logger(__name__)

#: Open jobs with fewer applicants than this are flagged as "low
#: applicant volume." A plain module constant rather than a Settings
#: field for now -- easy to promote to configurable later if a real
#: need shows up, not worth the indirection yet for one threshold.
LOW_APPLICANT_THRESHOLD = 5

DEFAULT_LIST_LIMIT = 10


class DashboardService:
    def __init__(
        self,
        db: AsyncSession,
        application_repository: ApplicationRepository | None = None,
        job_repository: JobRepository | None = None,
        email_repository: EmailRepository | None = None,
        resume_analysis_repository: ResumeAnalysisRepository | None = None,
        workflow_run_repository: WorkflowRunRepository | None = None,
        dashboard_brief_repository: DashboardBriefRepository | None = None,
        company_repository: CompanyRepository | None = None,
        agent: DashboardAgent | None = None,
    ) -> None:
        self._db = db
        self._applications = application_repository or ApplicationRepository(db)
        self._jobs = job_repository or JobRepository(db)
        self._emails = email_repository or EmailRepository(db)
        self._resume_analyses = resume_analysis_repository or ResumeAnalysisRepository(db)
        self._workflow_runs = workflow_run_repository or WorkflowRunRepository(db)
        self._briefs = dashboard_brief_repository or DashboardBriefRepository(db)
        self._companies = company_repository or CompanyRepository(db)
        self._agent = agent or DashboardAgent()

    async def get_dashboard(self, acting_user: User) -> "DashboardData":
        company_id = acting_user.company_id
        assert company_id is not None  # RBAC-gated to internal roles at the route layer

        awaiting_review = await self._applications.list_awaiting_review_for_company(
            company_id, limit=DEFAULT_LIST_LIMIT
        )
        low_applicant_jobs = await self._jobs.list_low_applicant_open_jobs(
            company_id, threshold=LOW_APPLICANT_THRESHOLD, limit=DEFAULT_LIST_LIMIT
        )
        recent_analyses = await self._resume_analyses.list_recent_completed_for_company(
            company_id, limit=DEFAULT_LIST_LIMIT
        )
        recent_workflow_runs = await self._workflow_runs.list_for_company(
            company_id, limit=DEFAULT_LIST_LIMIT
        )
        pending_drafts = await self._emails.list_recent_drafts_for_company(
            company_id, limit=DEFAULT_LIST_LIMIT
        )

        brief = await self._get_or_generate_daily_brief(
            acting_user=acting_user,
            awaiting_review=awaiting_review,
            low_applicant_jobs=low_applicant_jobs,
            recent_analyses=recent_analyses,
            pending_drafts=pending_drafts,
        )

        return DashboardData(
            brief=brief,
            awaiting_review=awaiting_review,
            low_applicant_jobs=low_applicant_jobs,
            recent_analyses=recent_analyses,
            recent_workflow_runs=recent_workflow_runs,
            pending_drafts=pending_drafts,
        )

    async def _get_or_generate_daily_brief(
        self,
        *,
        acting_user: User,
        awaiting_review: list[Application],
        low_applicant_jobs: list[tuple[Job, int]],
        recent_analyses: list[ResumeAnalysis],
        pending_drafts: list[Email],
    ) -> DashboardBrief | None:
        assert acting_user.company_id is not None
        today = datetime.now(UTC).date()

        existing = await self._briefs.get_for_company_and_date(acting_user.company_id, today)
        if existing is not None:
            return existing

        company = await self._companies.get_by_id(acting_user.company_id)
        assert company is not None  # FK guarantees this

        awaiting_review_facts = [self._application_to_fact(a) for a in awaiting_review]
        recent_analyses_facts = [self._analysis_to_fact(a) for a in recent_analyses]

        try:
            outcome = await self._agent.generate_daily_brief(
                recruiter_first_name=acting_user.first_name,
                company_name=company.name,
                pending_drafts_count=len(pending_drafts),
                awaiting_review=awaiting_review_facts,
                low_applicant_jobs=[
                    {"job_title": job.title, "applicant_count": str(count)}
                    for job, count in low_applicant_jobs
                ],
                recent_analyses=recent_analyses_facts,
            )
        except (LLMProviderError, InvalidStructuredOutputError):
            logger.exception(
                "dashboard_brief_generation_failed", company_id=str(acting_user.company_id)
            )
            return None

        known_application_ids = {f["application_id"] for f in awaiting_review_facts} | {
            f["application_id"] for f in recent_analyses_facts
        }
        recommended_actions = self._validate_recommended_actions(
            outcome.schema.recommended_actions, known_application_ids
        )

        brief = DashboardBrief(
            company_id=acting_user.company_id,
            brief_date=today,
            summary=outcome.schema.summary,
            recommended_actions=recommended_actions,
            llm_provider=outcome.llm_provider,
            llm_model=outcome.llm_model,
            prompt_version=outcome.prompt_version,
        )
        persisted = await self._briefs.create(brief)
        await self._db.commit()
        return persisted

    @staticmethod
    def _validate_recommended_actions(
        actions: list[RecommendedAction], known_application_ids: set[str]
    ) -> list[dict[str, str | None]]:
        """
        Anti-hallucination gate, same discipline as the Knowledge
        Agent's citation validation: a recommended action naming an
        application_id that wasn't actually in the facts handed to the
        LLM is a contract violation. Unlike Knowledge's all-or-nothing
        rejection (a factual answer with a fabricated citation is
        actively misleading), here the stakes are lower -- a suggestion
        list, not a grounded factual claim -- so an invalid
        application_id is stripped (set to null) rather than discarding
        the whole brief. The action's label text is kept either way.
        """
        validated = []
        for action in actions:
            application_id = action.application_id
            if application_id is not None and application_id not in known_application_ids:
                logger.warning(
                    "dashboard_brief_action_referenced_unknown_application",
                    application_id=application_id,
                )
                application_id = None
            validated.append({"label": action.label, "application_id": application_id})
        return validated

    @staticmethod
    def _application_to_fact(application: Application) -> dict[str, str]:
        days_waiting = (datetime.now(UTC) - application.created_at).days
        return {
            "application_id": str(application.id),
            "candidate_name": f"{application.candidate.first_name} {application.candidate.last_name}",
            "job_title": application.job.title,
            "days_waiting": str(days_waiting),
        }

    @staticmethod
    def _analysis_to_fact(analysis: ResumeAnalysis) -> dict[str, str]:
        return {
            "application_id": str(analysis.application_id),
            "candidate_name": (
                f"{analysis.application.candidate.first_name} "
                f"{analysis.application.candidate.last_name}"
            ),
            "job_title": analysis.application.job.title,
            "score": f"{analysis.overall_score:.1f}" if analysis.overall_score is not None else "n/a",
        }


class DashboardData:
    """Plain aggregate returned by get_dashboard -- the API layer maps
    this to DashboardRead. Not a Pydantic model itself since it carries
    live ORM instances (mapped to schemas at the API boundary, same
    pattern as every other service in this codebase)."""

    def __init__(
        self,
        *,
        brief: DashboardBrief | None,
        awaiting_review: list[Application],
        low_applicant_jobs: list[tuple[Job, int]],
        recent_analyses: list[ResumeAnalysis],
        recent_workflow_runs: list[WorkflowRun],
        pending_drafts: list[Email],
    ) -> None:
        self.brief = brief
        self.awaiting_review = awaiting_review
        self.low_applicant_jobs = low_applicant_jobs
        self.recent_analyses = recent_analyses
        self.recent_workflow_runs = recent_workflow_runs
        self.pending_drafts = pending_drafts
