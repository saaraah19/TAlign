"""
ResumeAnalysisService.

Orchestrates the full pipeline for one Application:

    ensure a completed ParsedResume exists (reusing one if possible)
    -> run alignment reasoning against the Job's requirements (fresh,
       always — alignment is job-specific, never reused)
    -> compute the score (scoring.py, zero LLM)
    -> persist a NEW ResumeAnalysis row (never update an existing one)

`run_analysis` is the target of the FastAPI BackgroundTasks call — it
takes only an `application_id` and opens its own DB session (see
`run_resume_analysis_task` at the bottom of this file), since a
background task runs after the request's own session has already
closed.

Failure handling: every failure that occurs AFTER a ParsedResume exists
(even a FAILED one) is persisted as a ResumeAnalysis row with
status=FAILED and an error_message — visible and queryable, never
silent. A failure in the deterministic text-extraction step (before any
ParsedResume could exist) is NOT represented as a ResumeAnalysis row at
all — it's surfaced via Resume.status=PARSE_FAILED one layer up, which
is where that failure actually happened. See
docs/04_slice4_resume_intelligence.md section D for the full reasoning.
"""

import uuid
from datetime import UTC, datetime

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.resume_intelligence.agent import JobRequirementsContext, ResumeIntelligenceAgent
from app.agents.resume_intelligence.schemas import (
    ExtractedEducation,
    ExtractedExperienceEntry,
    ExtractedResumeSchema,
)
from app.agents.resume_intelligence.scoring import compute_score
from app.core.exceptions import InvalidStructuredOutputError, LLMProviderError, NotFoundError
from app.models.application import Application
from app.models.parsed_resume import ParsedResume, ParsedResumeStatus
from app.models.resume import ResumeStatus
from app.models.resume_analysis import AnalysisProgressStatus, AnalysisStatus, ResumeAnalysis
from app.models.user import User
from app.repositories.application_repository import ApplicationRepository
from app.repositories.job_repository import JobRepository
from app.repositories.parsed_resume_repository import ParsedResumeRepository
from app.repositories.resume_analysis_repository import ResumeAnalysisRepository
from app.repositories.resume_repository import ResumeRepository
from app.services.resume_service import ResumeService

logger = structlog.get_logger(__name__)


class ResumeAnalysisService:
    def __init__(
        self,
        db: AsyncSession,
        analysis_repository: ResumeAnalysisRepository | None = None,
        application_repository: ApplicationRepository | None = None,
        resume_repository: ResumeRepository | None = None,
        parsed_resume_repository: ParsedResumeRepository | None = None,
        job_repository: JobRepository | None = None,
        resume_service: ResumeService | None = None,
        agent: ResumeIntelligenceAgent | None = None,
    ) -> None:
        self._db = db
        self._analyses = analysis_repository or ResumeAnalysisRepository(db)
        self._applications = application_repository or ApplicationRepository(db)
        self._resumes = resume_repository or ResumeRepository(db)
        self._parsed_resumes = parsed_resume_repository or ParsedResumeRepository(db)
        self._jobs = job_repository or JobRepository(db)
        self._resume_service = resume_service or ResumeService(db)
        self._agent = agent or ResumeIntelligenceAgent()

    # --- The pipeline itself ---

    async def run_analysis(self, application_id: uuid.UUID) -> ResumeAnalysis | None:
        """
        Runs (or re-runs) the full pipeline for one application's
        currently-attached resume. Returns None only in the case where
        there's nothing to analyze yet (no resume attached) — every
        other outcome, including every failure mode, is persisted.
        """
        application = await self._applications.get_by_id(application_id)
        if application is None:
            logger.error(
                "resume_analysis_application_not_found", application_id=str(application_id)
            )
            return None
        if application.resume_id is None:
            logger.warning(
                "resume_analysis_no_resume_attached", application_id=str(application_id)
            )
            return None

        resume = await self._resumes.get_by_id(application.resume_id)
        job = await self._jobs.get_by_id(application.job_id)
        if resume is None or job is None:
            logger.error(
                "resume_analysis_missing_resume_or_job", application_id=str(application_id)
            )
            return None

        try:
            parsed = await self._resume_service.ensure_parsed(resume=resume)
        except (LLMProviderError, InvalidStructuredOutputError) as exc:
            # ensure_parsed already persisted a FAILED ParsedResume row —
            # fetch its id so this ResumeAnalysis row can reference it.
            failed_parsed = await self._parsed_resumes.get_latest_for_resume(resume.id)
            assert failed_parsed is not None  # ensure_parsed guarantees this on this exception path
            return await self._persist_failed(
                application=application, parsed_resume_id=failed_parsed.id, error=str(exc)
            )
        except Exception:  # noqa: BLE001 — includes ResumeTextExtractionError; no ParsedResume exists
            # Deliberately NOT persisted as a ResumeAnalysis row — see module docstring.
            logger.exception(
                "resume_analysis_parsing_unavailable", application_id=str(application_id)
            )
            return None

        job_requirements = JobRequirementsContext(
            required_skills=job.required_skills,
            preferred_skills=job.preferred_skills,
            min_years_experience=job.min_years_experience,
            description=job.description,
        )
        extracted_schema = self._to_extracted_schema(parsed)

        try:
            alignment = await self._agent.reason_alignment(extracted_schema, job_requirements)
        except (LLMProviderError, InvalidStructuredOutputError) as exc:
            return await self._persist_failed(
                application=application, parsed_resume_id=parsed.id, error=str(exc)
            )

        score = compute_score(alignment.schema, min_years_experience=job.min_years_experience)

        analysis = ResumeAnalysis(
            application_id=application.id,
            parsed_resume_id=parsed.id,
            status=AnalysisStatus.COMPLETED.value,
            overall_score=score.overall_score,
            required_skills_score_pct=score.required_skills_score_pct,
            preferred_skills_score_pct=score.preferred_skills_score_pct,
            experience_score_pct=score.experience_score_pct,
            scoring_algorithm_version=score.algorithm_version,
            required_skills_result=[
                r.model_dump(mode="json") for r in alignment.schema.required_skills
            ],
            preferred_skills_result=[
                r.model_dump(mode="json") for r in alignment.schema.preferred_skills
            ],
            experience_fit=alignment.schema.experience_fit.model_dump(mode="json"),
            matched_skills=score.matched_skills,
            missing_skills=score.missing_skills,
            strengths=alignment.schema.strengths,
            potential_concerns=alignment.schema.potential_concerns,
            explanation=alignment.schema.explanation,
            llm_provider=alignment.llm_provider,
            llm_model=alignment.llm_model,
            prompt_version=alignment.prompt_version,
            analyzed_at=datetime.now(UTC),
        )
        persisted = await self._analyses.create(analysis)
        await self._db.commit()
        return persisted

    async def _persist_failed(
        self, *, application: Application, parsed_resume_id: uuid.UUID, error: str
    ) -> ResumeAnalysis:
        analysis = ResumeAnalysis(
            application_id=application.id,
            parsed_resume_id=parsed_resume_id,
            status=AnalysisStatus.FAILED.value,
            error_message=error,
        )
        persisted = await self._analyses.create(analysis)
        await self._db.commit()
        return persisted

    @staticmethod
    def _to_extracted_schema(parsed: ParsedResume) -> ExtractedResumeSchema:
        """Reconstructs the typed schema from a (possibly reused) ParsedResume ORM row."""
        return ExtractedResumeSchema(
            skills=parsed.extracted_skills,
            experience_entries=[
                ExtractedExperienceEntry.model_validate(e) for e in parsed.experience_entries
            ],
            total_years_experience=parsed.total_years_experience,
            education=[ExtractedEducation.model_validate(e) for e in parsed.education],
            certifications=parsed.certifications,
        )

    # --- Reads (recruiter-facing, company-scoped) ---

    async def get_latest_completed_for_company(
        self, *, application_id: uuid.UUID, acting_user: User
    ) -> ResumeAnalysis:
        await self._assert_application_in_company(application_id, acting_user.company_id)
        analysis = await self._analyses.get_latest_completed_for_application(application_id)
        if analysis is None:
            raise NotFoundError("No completed analysis is available for this application yet.")
        return analysis

    async def list_history_for_company(
        self, *, application_id: uuid.UUID, acting_user: User
    ) -> list[ResumeAnalysis]:
        await self._assert_application_in_company(application_id, acting_user.company_id)
        return await self._analyses.list_history_for_application(application_id)

    async def _assert_application_in_company(
        self, application_id: uuid.UUID, company_id: uuid.UUID
    ) -> None:
        application = await self._applications.get_by_id(application_id)
        if application is None or application.company_id != company_id:
            raise NotFoundError("Application not found.")

    # --- Progress status (both candidate- and recruiter-facing; status ONLY, never analysis content) ---

    async def get_progress_status(self, application: Application) -> AnalysisProgressStatus:
        """
        Derives a composite status from Resume/ParsedResume/ResumeAnalysis
        state — never returns analysis content, so this same method is
        safe to expose to BOTH candidates and recruiters (see
        app/api/v1/applications.py's two distinct endpoints, one per
        audience, both delegating to this one derivation).
        """
        if application.resume_id is None:
            return AnalysisProgressStatus.NOT_STARTED

        resume = await self._resumes.get_by_id(application.resume_id)
        if resume is None:
            return AnalysisProgressStatus.NOT_STARTED
        if resume.status == ResumeStatus.PARSE_FAILED.value:
            return AnalysisProgressStatus.FAILED

        completed_parsed = await self._parsed_resumes.get_latest_completed_for_resume(resume.id)
        if completed_parsed is None:
            latest_parsed = await self._parsed_resumes.get_latest_for_resume(resume.id)
            if (
                latest_parsed is not None
                and latest_parsed.status == ParsedResumeStatus.FAILED.value
            ):
                return AnalysisProgressStatus.FAILED
            return AnalysisProgressStatus.PARSING

        latest_analysis = await self._analyses.get_latest_for_application(application.id)
        if latest_analysis is None:
            return AnalysisProgressStatus.ANALYZING
        if latest_analysis.status == AnalysisStatus.FAILED.value:
            return AnalysisProgressStatus.FAILED
        return AnalysisProgressStatus.COMPLETE


async def run_resume_analysis_task(application_id: uuid.UUID) -> None:
    """
    FastAPI BackgroundTasks entrypoint. Opens its OWN database session —
    a background task runs after the triggering request's session has
    already closed, so it cannot reuse `Depends(get_db)`'s session.
    """
    from app.database.session import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        service = ResumeAnalysisService(db)
        try:
            await service.run_analysis(application_id)
        except Exception:  # noqa: BLE001 — background tasks must never raise past this point
            logger.exception(
                "resume_analysis_background_task_failed", application_id=str(application_id)
            )
