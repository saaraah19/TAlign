"""
Tests for ResumeIntelligenceAgent, using FakeLLMProvider — no live
Gemini call anywhere in this file. Covers the failure modes explicitly
required: LLM provider failure, malformed structured output (with the
one-retry behavior), and prompt version persistence.
"""

import pytest

from app.agents.resume_intelligence.agent import JobRequirementsContext, ResumeIntelligenceAgent
from app.agents.resume_intelligence.prompts import (
    ALIGNMENT_PROMPT_VERSION,
    EXTRACTION_PROMPT_VERSION,
)
from app.agents.resume_intelligence.schemas import (
    AlignmentReasoningSchema,
    ExperienceFitResult,
    ExtractedResumeSchema,
    SkillMatchResult,
)
from app.core.exceptions import InvalidStructuredOutputError, LLMProviderError
from app.models.resume_analysis import MatchState
from tests.fakes import FakeLLMProvider

_SAMPLE_EXTRACTION = ExtractedResumeSchema(
    skills=["Python", "SQL"],
    experience_entries=[],
    total_years_experience=3.0,
)

_SAMPLE_ALIGNMENT = AlignmentReasoningSchema(
    required_skills=[SkillMatchResult(skill="Python", match_state=MatchState.MATCHED)],
    preferred_skills=[],
    experience_fit=ExperienceFitResult(
        meets_minimum=True, justification="3 years, meets 2 year minimum"
    ),
    strengths=["Strong Python background"],
    potential_concerns=[],
    explanation="Good alignment overall.",
)


async def test_extract_returns_schema_and_provenance() -> None:
    fake = FakeLLMProvider(structured_responses=[_SAMPLE_EXTRACTION])
    agent = ResumeIntelligenceAgent(llm_provider=fake)

    outcome = await agent.extract("some resume text")

    assert outcome.schema == _SAMPLE_EXTRACTION
    assert outcome.prompt_version == EXTRACTION_PROMPT_VERSION
    assert outcome.llm_provider == "fakellm"


async def test_reason_alignment_returns_schema_and_provenance() -> None:
    fake = FakeLLMProvider(structured_responses=[_SAMPLE_ALIGNMENT])
    agent = ResumeIntelligenceAgent(llm_provider=fake)
    job_requirements = JobRequirementsContext(
        required_skills=["Python"], preferred_skills=[], min_years_experience=2, description="..."
    )

    outcome = await agent.reason_alignment(_SAMPLE_EXTRACTION, job_requirements)

    assert outcome.schema == _SAMPLE_ALIGNMENT
    assert outcome.prompt_version == ALIGNMENT_PROMPT_VERSION


async def test_provider_failure_propagates_without_retry() -> None:
    """LLMProviderError (network/timeout/rate-limit) is never retried — see agent docstring."""
    fake = FakeLLMProvider(structured_responses=[LLMProviderError("simulated network failure")])
    agent = ResumeIntelligenceAgent(llm_provider=fake)

    with pytest.raises(LLMProviderError):
        await agent.extract("some resume text")

    assert len(fake.calls) == 1  # no retry attempted


async def test_malformed_output_is_retried_once_then_succeeds() -> None:
    fake = FakeLLMProvider(
        structured_responses=[
            InvalidStructuredOutputError("first attempt: bad json"),
            _SAMPLE_EXTRACTION,
        ]
    )
    agent = ResumeIntelligenceAgent(llm_provider=fake)

    outcome = await agent.extract("some resume text")

    assert outcome.schema == _SAMPLE_EXTRACTION
    assert len(fake.calls) == 2  # original + one retry


async def test_malformed_output_fails_permanently_after_one_retry() -> None:
    fake = FakeLLMProvider(
        structured_responses=[
            InvalidStructuredOutputError("first attempt: bad json"),
            InvalidStructuredOutputError("second attempt: still bad json"),
        ]
    )
    agent = ResumeIntelligenceAgent(llm_provider=fake)

    with pytest.raises(InvalidStructuredOutputError):
        await agent.extract("some resume text")

    assert len(fake.calls) == 2  # original + exactly one retry, then gives up


async def test_explain_grounds_in_provided_analysis_data() -> None:
    fake = FakeLLMProvider(text_response="This candidate scored well on required skills.")
    agent = ResumeIntelligenceAgent(llm_provider=fake)

    message = await agent.explain(
        analysis={
            "overall_score": 78.0,
            "required_skills_result": [],
            "preferred_skills_result": [],
            "experience_fit": {},
            "strengths": [],
            "potential_concerns": [],
            "explanation": "",
        },
        question="Why did this candidate score 78?",
        audience_role="recruiter",
    )

    assert message == "This candidate scored well on required skills."
    assert len(fake.calls) == 1
    # The question and the score must actually reach the prompt.
    sent_content = " ".join(m.content for m in fake.calls[0])
    assert "78" in sent_content
    assert "Why did this candidate score 78?" in sent_content


async def test_explain_wraps_provider_failure() -> None:
    fake = FakeLLMProvider(text_response=RuntimeError("provider is down"))
    agent = ResumeIntelligenceAgent(llm_provider=fake)

    with pytest.raises(LLMProviderError):
        await agent.explain(
            analysis={
                "overall_score": 50.0,
                "required_skills_result": [],
                "preferred_skills_result": [],
                "experience_fit": {},
                "strengths": [],
                "potential_concerns": [],
                "explanation": "",
            },
            question="test",
            audience_role="recruiter",
        )
