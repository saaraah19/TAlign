"""
CommunicationAgent.

Two typed methods, matching the two email types this MVP slice covers
(see docs/05_slice5_communication_agent.md for the two-type scope
decision — follow-up/reminder/offer/onboarding are deferred).

Hard boundary, same shape as ResumeIntelligenceAgent's: this agent's
responsibility ends at producing a draft subject/body. It never:
  - sends an email (no SMTP/Gmail integration exists anywhere in this
    codebase — see app/models/email.py's docstring)
  - decides whether a candidate should be rejected or invited (that
    decision was already made by a human, via the Application status
    transition, before this agent is ever invoked)
  - queries the database directly (it receives plain data — names,
    titles, an optional strengths list — never a DB session or a
    service; CommunicationService is the caller and the only thing
    that touches the database)

Not registered in the Agent Registry / Compass Capability Registry in
this slice — unlike ResumeIntelligenceAgent's `explain_analysis`
capability, drafting an email is a generation action triggered by an
explicit recruiter button click (CommunicationService, called directly
from app/api/v1/communication.py), not a narration of already-stored
data that fits Compass's chat-style "ask a question" shape. Wiring
"ask Compass to draft this" is a reasonable future enhancement, not
built here — see the slice's scope notes.
"""

from dataclasses import dataclass

from app.agents.communication.prompts import (
    INTERVIEW_INVITATION_PROMPT_VERSION,
    ONBOARDING_WELCOME_PROMPT_VERSION,
    REJECTION_PROMPT_VERSION,
    build_interview_invitation_prompt,
    build_rejection_prompt,
    build_welcome_email_prompt,
)
from app.agents.communication.schemas import DraftEmailSchema
from app.agents.shared.structured_output import complete_structured_with_one_retry
from app.core.llm_provider import LLMProvider, get_llm_provider


@dataclass(frozen=True)
class DraftOutcome:
    schema: DraftEmailSchema
    llm_provider: str
    llm_model: str
    prompt_version: str


class CommunicationAgent:
    def __init__(self, llm_provider: LLMProvider | None = None) -> None:
        self._llm = llm_provider or get_llm_provider()

    async def draft_rejection(
        self,
        *,
        candidate_first_name: str,
        job_title: str,
        company_name: str,
        strengths: list[str] | None = None,
    ) -> DraftOutcome:
        messages = build_rejection_prompt(
            candidate_first_name=candidate_first_name,
            job_title=job_title,
            company_name=company_name,
            strengths=strengths,
        )
        schema = await complete_structured_with_one_retry(self._llm, messages, DraftEmailSchema)
        return DraftOutcome(
            schema=schema,
            llm_provider=self._provider_name(),
            llm_model=self._model_name(),
            prompt_version=REJECTION_PROMPT_VERSION,
        )

    async def draft_interview_invitation(
        self, *, candidate_first_name: str, job_title: str, company_name: str
    ) -> DraftOutcome:
        messages = build_interview_invitation_prompt(
            candidate_first_name=candidate_first_name,
            job_title=job_title,
            company_name=company_name,
        )
        schema = await complete_structured_with_one_retry(self._llm, messages, DraftEmailSchema)
        return DraftOutcome(
            schema=schema,
            llm_provider=self._provider_name(),
            llm_model=self._model_name(),
            prompt_version=INTERVIEW_INVITATION_PROMPT_VERSION,
        )

    async def draft_welcome_email(
        self, *, candidate_first_name: str, job_title: str, company_name: str
    ) -> DraftOutcome:
        """
        Called by the Workflow Engine's hire workflow (via
        CommunicationService.generate_system_draft) — not by a recruiter
        button click. See build_welcome_email_prompt's docstring: the
        content-safety signature discipline is identical either way.
        """
        messages = build_welcome_email_prompt(
            candidate_first_name=candidate_first_name,
            job_title=job_title,
            company_name=company_name,
        )
        schema = await complete_structured_with_one_retry(self._llm, messages, DraftEmailSchema)
        return DraftOutcome(
            schema=schema,
            llm_provider=self._provider_name(),
            llm_model=self._model_name(),
            prompt_version=ONBOARDING_WELCOME_PROMPT_VERSION,
        )

    def _provider_name(self) -> str:
        return type(self._llm).__name__.replace("Provider", "").lower()

    def _model_name(self) -> str:
        return getattr(self._llm, "_default_model", "unknown")
