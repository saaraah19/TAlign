"""
ResumeIntelligenceAgent.

Two typed methods, matching the two separate LLM calls in the pipeline:
  - `extract`: raw resume text -> ExtractedResumeSchema (no job context
    involved at all — this is the reusable-across-applications step,
    see app/models/parsed_resume.py).
  - `reason_alignment`: ExtractedResumeSchema + job requirements ->
    AlignmentReasoningSchema (no score — see scoring.py for that step,
    deliberately NOT performed here).

Callers: `ResumeAnalysisService` calls `extract`/`reason_alignment`
DIRECTLY (constructing its own `ResumeIntelligenceAgent()` instance) —
not through the Agent Registry / Compass's generic `run()` dispatch.
That generic path exists for a different purpose: Compass's
`explain_analysis` capability calls `agent.run(context)`, which
delegates to `explain()` — narrating an EXISTING stored analysis, not
producing new intelligence. Both call shapes live on one agent instance
because they share one LLM-call/versioning setup and conceptually belong
to the same "resume intelligence" capability — see
docs/04_slice4_resume_intelligence.md section E for the full reasoning
on why this isn't two separate registry entries.

Hard boundary (explicit product requirement): this agent's
responsibility ends at producing structured intelligence. It never:
  - computes overall_score (scoring.py, called by the SERVICE, does that)
  - decides accept/reject
  - moves an Application through its pipeline
  - queries the database directly (it receives plain data — resume
    text, a JobRequirementsContext dataclass — never a DB session or
    a service)
"""

from dataclasses import dataclass

import structlog

from app.agents.base import Agent, AgentContext, AgentResult
from app.agents.resume_intelligence.prompts import (
    ALIGNMENT_PROMPT_VERSION,
    EXTRACTION_PROMPT_VERSION,
    build_alignment_prompt,
    build_explanation_prompt,
    build_extraction_prompt,
)
from app.agents.resume_intelligence.schemas import AlignmentReasoningSchema, ExtractedResumeSchema
from app.core.exceptions import InvalidStructuredOutputError, LLMProviderError
from app.core.llm_provider import LLMMessage, LLMProvider, get_llm_provider

logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class JobRequirementsContext:
    """
    Structured job requirements passed to the agent — never a Job ORM
    row. `description` is included explicitly labeled as CONTEXT, not
    criteria; only the three structured fields are the official scoring
    checklist. See app/agents/resume_intelligence/prompts.py for exactly
    how this distinction is enforced in the prompt text itself.
    """

    required_skills: list[str]
    preferred_skills: list[str]
    min_years_experience: int | None
    description: str


@dataclass(frozen=True)
class ExtractionOutcome:
    schema: ExtractedResumeSchema
    llm_provider: str
    llm_model: str
    prompt_version: str


@dataclass(frozen=True)
class AlignmentOutcome:
    schema: AlignmentReasoningSchema
    llm_provider: str
    llm_model: str
    prompt_version: str


class ResumeIntelligenceAgent(Agent):
    #: Registered under this name in the Agent Registry — matches the
    #: Compass capability it serves via `run()`. See module docstring
    #: for why `extract`/`reason_alignment` bypass the registry entirely.
    name = "explain_analysis"

    def __init__(self, llm_provider: LLMProvider | None = None) -> None:
        self._llm = llm_provider or get_llm_provider()

    async def extract(self, resume_text: str) -> ExtractionOutcome:
        messages = build_extraction_prompt(resume_text)
        schema = await self._complete_structured_with_retry(messages, ExtractedResumeSchema)
        return ExtractionOutcome(
            schema=schema,
            llm_provider=self._provider_name(),
            llm_model=self._model_name(),
            prompt_version=EXTRACTION_PROMPT_VERSION,
        )

    async def reason_alignment(
        self, extracted: ExtractedResumeSchema, job_requirements: JobRequirementsContext
    ) -> AlignmentOutcome:
        experience_summary = self._summarize_experience(extracted)
        messages = build_alignment_prompt(
            extracted_skills=extracted.skills,
            experience_summary=experience_summary,
            total_years_experience=extracted.total_years_experience,
            required_skills=job_requirements.required_skills,
            preferred_skills=job_requirements.preferred_skills,
            min_years_experience=job_requirements.min_years_experience,
            job_description_context=job_requirements.description,
        )
        schema = await self._complete_structured_with_retry(messages, AlignmentReasoningSchema)
        return AlignmentOutcome(
            schema=schema,
            llm_provider=self._provider_name(),
            llm_model=self._model_name(),
            prompt_version=ALIGNMENT_PROMPT_VERSION,
        )

    async def explain(self, *, analysis: dict, question: str, audience_role: str) -> str:
        """Narrates an EXISTING stored analysis. Never introduces new judgments or a new score."""
        messages = build_explanation_prompt(
            question=question, audience_role=audience_role, **analysis
        )
        try:
            response = await self._llm.complete(messages, temperature=0.3)
        except Exception as exc:  # noqa: BLE001 — wrap any provider failure uniformly
            raise LLMProviderError(f"Resume Intelligence explanation call failed: {exc}") from exc
        return response.content

    async def run(self, context: AgentContext) -> AgentResult:
        """
        Generic Agent Registry entrypoint — used only by Compass's
        `explain_analysis` capability (see compass/context_builder.py,
        which populates `context.payload` before this runs).
        """
        payload = context.payload
        message = await self.explain(
            analysis=payload["analysis"],
            question=payload["question"],
            audience_role=payload["audience_role"],
        )
        return AgentResult(
            output={"message": message},
            reasoning="Grounded narration of a stored ResumeAnalysis; no new judgments introduced.",
            confidence=None,
        )

    async def _complete_structured_with_retry(self, messages: list[LLMMessage], schema_cls):
        """
        Exactly one re-prompt retry, and only for schema-validation
        failures — never for LLMProviderError (network/timeout/rate
        limit), which propagates immediately. This is a single
        micro-retry within one LLM call, distinct from the "automatic
        retry loop / backoff queue" explicitly excluded from V1 — that
        refers to background-job-level retries, which this codebase
        never does automatically (see ResumeAnalysisService — failures
        there are terminal until a user explicitly re-triggers).
        """
        try:
            return await self._llm.complete_structured(messages, response_schema=schema_cls)
        except InvalidStructuredOutputError as first_error:
            logger.warning(
                "structured_output_retry", schema=schema_cls.__name__, error=str(first_error)
            )
            retry_messages = [
                *messages,
                LLMMessage(
                    role="user",
                    content=(
                        "Your previous response did not match the required schema. "
                        "Respond again, strictly matching the schema and nothing else."
                    ),
                ),
            ]
            try:
                return await self._llm.complete_structured(
                    retry_messages, response_schema=schema_cls
                )
            except InvalidStructuredOutputError as second_error:
                raise InvalidStructuredOutputError(
                    f"LLM did not return valid {schema_cls.__name__} output after one retry: "
                    f"{second_error}"
                ) from second_error

    @staticmethod
    def _summarize_experience(extracted: ExtractedResumeSchema) -> str:
        if not extracted.experience_entries:
            return "No experience entries extracted."
        parts = []
        for entry in extracted.experience_entries:
            end = "present" if entry.is_current else (entry.end_date or "unknown end date")
            parts.append(
                f"{entry.title} at {entry.company or 'unknown company'} "
                f"({entry.start_date or 'unknown start'} - {end})"
            )
        return "; ".join(parts)

    def _provider_name(self) -> str:
        return type(self._llm).__name__.replace("Provider", "").lower()

    def _model_name(self) -> str:
        return getattr(self._llm, "_default_model", "unknown")
