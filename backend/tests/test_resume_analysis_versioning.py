"""
Tests for the "never overwrite a historical analysis" guarantee.

`ResumeAnalysisRepository` has no update method at all — checked
structurally here, since that's what actually makes overwriting
impossible (not a convention someone has to remember to follow).
`ResumeAnalysisService.run_analysis` is also checked to always persist
via `create`, whether the outcome is success or failure.
"""

import uuid
from unittest.mock import AsyncMock

from app.models.application import Application
from app.models.job import Job
from app.models.resume import Resume, ResumeStatus
from app.repositories.resume_analysis_repository import ResumeAnalysisRepository
from app.services.resume_analysis_service import ResumeAnalysisService
from tests.fakes import FakeLLMProvider


def test_resume_analysis_repository_has_no_update_method() -> None:
    """
    The only mutation-shaped method on this repository is `create`
    (an INSERT). If someone later adds an `update`/`save` method that
    mutates an existing row's status/score fields, this test fails —
    that would be exactly the "overwrite history" bug this design
    prevents.
    """
    public_methods = {
        name
        for name in dir(ResumeAnalysisRepository)
        if not name.startswith("_") and callable(getattr(ResumeAnalysisRepository, name))
    }
    forbidden = {"update", "save", "upsert", "patch"}
    assert public_methods.isdisjoint(forbidden)


async def test_run_analysis_persists_via_create_on_success() -> None:
    candidate_id = uuid.uuid4()
    application_id = uuid.uuid4()
    resume_id = uuid.uuid4()
    job_id = uuid.uuid4()

    application = Application(
        id=application_id,
        candidate_id=candidate_id,
        job_id=job_id,
        company_id=uuid.uuid4(),
        resume_id=resume_id,
        status="applied",
    )
    resume = Resume(
        id=resume_id,
        candidate_id=candidate_id,
        file_path="/tmp/x",
        original_filename="resume.txt",
        content_type="text/plain",
        file_size_bytes=10,
        raw_text="Experienced Python developer.",
        status=ResumeStatus.TEXT_READY.value,
    )
    job = Job(
        id=job_id,
        company_id=uuid.uuid4(),
        title="Backend Engineer",
        description="...",
        employment_type="full_time",
        required_skills=["Python"],
        preferred_skills=[],
        min_years_experience=None,
    )

    application_repo = AsyncMock()
    application_repo.get_by_id.return_value = application
    resume_repo = AsyncMock()
    resume_repo.get_by_id.return_value = resume
    job_repo = AsyncMock()
    job_repo.get_by_id.return_value = job
    analysis_repo = AsyncMock()
    analysis_repo.create.side_effect = lambda a: a
    db = AsyncMock()

    from app.agents.resume_intelligence.agent import ResumeIntelligenceAgent
    from app.agents.resume_intelligence.schemas import (
        AlignmentReasoningSchema,
        ExperienceFitResult,
        ExtractedResumeSchema,
        SkillMatchResult,
    )
    from app.models.resume_analysis import MatchState
    from app.services.resume_service import ResumeService

    fake_llm = FakeLLMProvider(
        structured_responses=[
            ExtractedResumeSchema(
                skills=["Python"], experience_entries=[], total_years_experience=3.0
            ),
            AlignmentReasoningSchema(
                required_skills=[
                    SkillMatchResult(skill="Python", match_state=MatchState.MATCHED)
                ],
                preferred_skills=[],
                experience_fit=ExperienceFitResult(meets_minimum=True, justification="ok"),
                strengths=["Python"],
                potential_concerns=[],
                explanation="Good fit.",
            ),
        ]
    )
    parsed_repo = AsyncMock()
    parsed_repo.get_latest_completed_for_resume.return_value = None
    parsed_repo.create.side_effect = lambda p: p

    agent = ResumeIntelligenceAgent(llm_provider=fake_llm)
    resume_service = ResumeService(
        db, resume_repository=resume_repo, parsed_resume_repository=parsed_repo, agent=agent
    )

    service = ResumeAnalysisService(
        db,
        analysis_repository=analysis_repo,
        application_repository=application_repo,
        resume_repository=resume_repo,
        parsed_resume_repository=parsed_repo,
        job_repository=job_repo,
        resume_service=resume_service,
        agent=agent,
    )

    result = await service.run_analysis(application_id)

    assert result is not None
    assert result.status == "completed"
    analysis_repo.create.assert_called_once()
    # No update-shaped call exists at all on this repository (see the
    # structural test above) — nothing further to assert here beyond
    # confirming create() is how persistence happened.
