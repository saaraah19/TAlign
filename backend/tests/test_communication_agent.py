"""
Tests for CommunicationAgent, using FakeLLMProvider — no live Gemini
call anywhere in this file. Same pattern as
test_resume_intelligence_agent.py, adapted for the shared retry helper.
"""

import pytest

from app.agents.communication.agent import CommunicationAgent
from app.agents.communication.prompts import (
    INTERVIEW_INVITATION_PROMPT_VERSION,
    ONBOARDING_WELCOME_PROMPT_VERSION,
    REJECTION_PROMPT_VERSION,
)
from app.agents.communication.schemas import DraftEmailSchema
from app.core.exceptions import InvalidStructuredOutputError, LLMProviderError
from tests.fakes import FakeLLMProvider

_SAMPLE_DRAFT = DraftEmailSchema(
    subject="Update on your application",
    body="Thank you for your interest — we've decided to move forward with other candidates.",
)


async def test_draft_rejection_returns_schema_and_provenance() -> None:
    fake = FakeLLMProvider(structured_responses=[_SAMPLE_DRAFT])
    agent = CommunicationAgent(llm_provider=fake)

    outcome = await agent.draft_rejection(
        candidate_first_name="Ahmed", job_title="Backend Engineer", company_name="Talign"
    )

    assert outcome.schema == _SAMPLE_DRAFT
    assert outcome.prompt_version == REJECTION_PROMPT_VERSION
    assert outcome.llm_provider == "fakellm"


async def test_draft_interview_invitation_returns_schema_and_provenance() -> None:
    fake = FakeLLMProvider(structured_responses=[_SAMPLE_DRAFT])
    agent = CommunicationAgent(llm_provider=fake)

    outcome = await agent.draft_interview_invitation(
        candidate_first_name="Lina", job_title="Data Analyst", company_name="Talign"
    )

    assert outcome.schema == _SAMPLE_DRAFT
    assert outcome.prompt_version == INTERVIEW_INVITATION_PROMPT_VERSION


async def test_provider_failure_propagates_without_retry() -> None:
    fake = FakeLLMProvider(structured_responses=[LLMProviderError("simulated network failure")])
    agent = CommunicationAgent(llm_provider=fake)

    with pytest.raises(LLMProviderError):
        await agent.draft_rejection(
            candidate_first_name="Ahmed", job_title="Backend Engineer", company_name="Talign"
        )

    assert len(fake.calls) == 1  # no retry attempted


async def test_malformed_output_is_retried_once_then_succeeds() -> None:
    fake = FakeLLMProvider(
        structured_responses=[
            InvalidStructuredOutputError("first attempt: bad json"),
            _SAMPLE_DRAFT,
        ]
    )
    agent = CommunicationAgent(llm_provider=fake)

    outcome = await agent.draft_rejection(
        candidate_first_name="Ahmed", job_title="Backend Engineer", company_name="Talign"
    )

    assert outcome.schema == _SAMPLE_DRAFT
    assert len(fake.calls) == 2  # original + one retry


async def test_malformed_output_fails_permanently_after_one_retry() -> None:
    fake = FakeLLMProvider(
        structured_responses=[
            InvalidStructuredOutputError("first attempt: bad json"),
            InvalidStructuredOutputError("second attempt: still bad json"),
        ]
    )
    agent = CommunicationAgent(llm_provider=fake)

    with pytest.raises(InvalidStructuredOutputError):
        await agent.draft_rejection(
            candidate_first_name="Ahmed", job_title="Backend Engineer", company_name="Talign"
        )

    assert len(fake.calls) == 2


async def test_draft_welcome_email_returns_schema_and_provenance() -> None:
    """
    Slice 7 addition: draft_welcome_email is called by the Workflow
    Engine's hire workflow, not a recruiter button click, but the Agent
    boundary itself is unchanged — same schema, same retry helper.
    """
    fake = FakeLLMProvider(structured_responses=[_SAMPLE_DRAFT])
    agent = CommunicationAgent(llm_provider=fake)

    outcome = await agent.draft_welcome_email(
        candidate_first_name="Ahmed", job_title="Backend Engineer", company_name="Talign"
    )

    assert outcome.schema == _SAMPLE_DRAFT
    assert outcome.prompt_version == ONBOARDING_WELCOME_PROMPT_VERSION


async def test_rejection_prompt_includes_strengths_when_provided() -> None:
    fake = FakeLLMProvider(structured_responses=[_SAMPLE_DRAFT])
    agent = CommunicationAgent(llm_provider=fake)

    await agent.draft_rejection(
        candidate_first_name="Ahmed",
        job_title="Backend Engineer",
        company_name="Talign",
        strengths=["Strong Python background"],
    )

    sent_content = " ".join(m.content for m in fake.calls[0])
    assert "Strong Python background" in sent_content
