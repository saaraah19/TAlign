"""
ResumeService.

Owns the Resume and ParsedResume lifecycle. Two distinct kinds of work,
kept in the same service because they're both "prepare a resume for
alignment analysis," but implemented as clearly separate methods:

  - `upload_resume`: pure I/O — validate, store the file, extract raw
    text deterministically (pypdf/python-docx). No LLM call.
  - `ensure_parsed`: the ONE LLM call that turns raw text into
    structured skills/experience (ParsedResume). Reuses an existing
    completed ParsedResume if one exists for this resume — only calls
    the agent when there isn't one yet, or `force_reparse=True` is
    passed explicitly.
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.resume_intelligence.agent import ResumeIntelligenceAgent
from app.core.config import settings
from app.core.exceptions import (
    FileTooLargeError,
    InvalidCandidateError,
    InvalidStructuredOutputError,
    LLMProviderError,
    NotFoundError,
    ResumeTextExtractionError,
    UnsupportedFileTypeError,
)
from app.core.roles import AccountType
from app.models.parsed_resume import ParsedResume, ParsedResumeStatus
from app.models.resume import Resume, ResumeStatus
from app.models.user import User
from app.repositories.parsed_resume_repository import ParsedResumeRepository
from app.repositories.resume_repository import ResumeRepository
from app.utils.local_file_storage import save_resume_file
from app.utils.resume_text_extraction import extract_text


class ResumeService:
    def __init__(
        self,
        db: AsyncSession,
        resume_repository: ResumeRepository | None = None,
        parsed_resume_repository: ParsedResumeRepository | None = None,
        agent: ResumeIntelligenceAgent | None = None,
    ) -> None:
        self._db = db
        self._resumes = resume_repository or ResumeRepository(db)
        self._parsed_resumes = parsed_resume_repository or ParsedResumeRepository(db)
        self._agent = agent or ResumeIntelligenceAgent()

    # --- Upload (deterministic) ---

    async def upload_resume(
        self, *, candidate: User, filename: str, content_type: str, content: bytes
    ) -> Resume:
        self._assert_valid_candidate(candidate)
        self._assert_valid_file(content_type=content_type, size=len(content))

        file_path = save_resume_file(candidate_id=candidate.id, filename=filename, content=content)

        resume = Resume(
            candidate_id=candidate.id,
            file_path=file_path,
            original_filename=filename,
            content_type=content_type,
            file_size_bytes=len(content),
            status=ResumeStatus.UPLOADED.value,
        )

        try:
            raw_text = extract_text(content_type=content_type, content=content)
            resume.raw_text = raw_text
            resume.status = ResumeStatus.TEXT_READY.value
        except ResumeTextExtractionError as exc:
            resume.status = ResumeStatus.PARSE_FAILED.value
            resume.parse_error = str(exc)

        resume = await self._resumes.create(resume)
        await self._db.commit()
        return resume

    async def get_my_resume(self, *, resume_id: uuid.UUID, candidate: User) -> Resume:
        resume = await self._resumes.get_by_id_for_candidate(resume_id, candidate.id)
        if resume is None:
            raise NotFoundError("Resume not found.")
        return resume

    async def list_my_resumes(self, *, candidate: User) -> list[Resume]:
        return await self._resumes.list_for_candidate(candidate.id)

    # --- Parsing (the one LLM extraction call, reused where possible) ---

    async def ensure_parsed(self, *, resume: Resume, force_reparse: bool = False) -> ParsedResume:
        """
        Returns a completed ParsedResume for this resume, reusing an
        existing one unless `force_reparse` is set or none exists yet.
        Raises if the resume's deterministic text extraction never
        succeeded (nothing to parse) or the LLM call fails.
        """
        if resume.status != ResumeStatus.TEXT_READY.value:
            raise ResumeTextExtractionError(
                "This resume's text could not be extracted, so it cannot be parsed. "
                "Please re-upload a valid PDF, DOCX, or TXT file."
            )

        if not force_reparse:
            existing = await self._parsed_resumes.get_latest_completed_for_resume(resume.id)
            if existing is not None:
                return existing

        assert resume.raw_text is not None  # guaranteed by TEXT_READY status above

        try:
            outcome = await self._agent.extract(resume.raw_text)
            parsed = ParsedResume(
                resume_id=resume.id,
                extracted_skills=outcome.schema.skills,
                experience_entries=[e.model_dump() for e in outcome.schema.experience_entries],
                total_years_experience=outcome.schema.total_years_experience,
                education=[e.model_dump() for e in outcome.schema.education],
                certifications=outcome.schema.certifications,
                llm_provider=outcome.llm_provider,
                llm_model=outcome.llm_model,
                prompt_version=outcome.prompt_version,
                status=ParsedResumeStatus.COMPLETED.value,
            )
        except (LLMProviderError, InvalidStructuredOutputError) as exc:
            parsed = ParsedResume(
                resume_id=resume.id,
                llm_provider="unknown",
                llm_model="unknown",
                prompt_version="unknown",
                status=ParsedResumeStatus.FAILED.value,
                error_message=str(exc),
            )
            await self._parsed_resumes.create(parsed)
            await self._db.commit()
            raise

        parsed = await self._parsed_resumes.create(parsed)
        await self._db.commit()
        return parsed

    @staticmethod
    def _assert_valid_candidate(user: User) -> None:
        if user.account_type != AccountType.CANDIDATE.value:
            raise InvalidCandidateError("Only candidate accounts can upload resumes.")

    @staticmethod
    def _assert_valid_file(*, content_type: str, size: int) -> None:
        if content_type not in settings.allowed_resume_content_types:
            raise UnsupportedFileTypeError(
                f"Unsupported file type '{content_type}'. Allowed types: "
                f"{', '.join(settings.allowed_resume_content_types)}."
            )
        if size > settings.max_resume_file_size_bytes:
            max_mb = settings.max_resume_file_size_bytes / (1024 * 1024)
            raise FileTooLargeError(f"File exceeds the maximum allowed size of {max_mb:.1f} MB.")
