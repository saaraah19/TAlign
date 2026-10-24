"""
Tests for KnowledgeAgent, using FakeLLMProvider — no live Gemini call
anywhere in this file. Same pattern as test_communication_agent.py.
"""

import uuid

import pytest

from app.agents.knowledge.agent import KnowledgeAgent
from app.agents.knowledge.prompts import KNOWLEDGE_ANSWER_PROMPT_VERSION
from app.agents.knowledge.schemas import Citation, KnowledgeAnswerSchema, RetrievedChunk
from app.core.exceptions import InvalidStructuredOutputError, LLMProviderError
from tests.fakes import FakeLLMProvider

_CHUNK_ID = uuid.uuid4()
_DOCUMENT_ID = uuid.uuid4()

_SAMPLE_CHUNKS = [
    RetrievedChunk(
        chunk_id=_CHUNK_ID,
        document_id=_DOCUMENT_ID,
        document_title="Leave Policy",
        content="Employees accrue 25 days of annual leave per year.",
    )
]

_GROUNDED_ANSWER = KnowledgeAnswerSchema(
    answer="You accrue 25 days of annual leave per year.",
    citations=[
        Citation(
            document_id=_DOCUMENT_ID,
            document_title="Leave Policy",
            chunk_id=_CHUNK_ID,
            excerpt="Employees accrue 25 days of annual leave per year.",
        )
    ],
    grounded=True,
)

_UNGROUNDED_ANSWER = KnowledgeAnswerSchema(
    answer="The available documents don't cover this topic.",
    citations=[],
    grounded=False,
)


async def test_answer_question_returns_schema_and_provenance() -> None:
    fake = FakeLLMProvider(structured_responses=[_GROUNDED_ANSWER])
    agent = KnowledgeAgent(llm_provider=fake)

    outcome = await agent.answer_question(
        question="How many leave days do I get?", chunks=_SAMPLE_CHUNKS
    )

    assert outcome.schema == _GROUNDED_ANSWER
    assert outcome.prompt_version == KNOWLEDGE_ANSWER_PROMPT_VERSION
    assert outcome.llm_provider == "fakellm"


async def test_answer_question_can_return_ungrounded_answer() -> None:
    fake = FakeLLMProvider(structured_responses=[_UNGROUNDED_ANSWER])
    agent = KnowledgeAgent(llm_provider=fake)

    outcome = await agent.answer_question(
        question="What's the parking policy?", chunks=_SAMPLE_CHUNKS
    )

    assert outcome.schema.grounded is False
    assert outcome.schema.citations == []


async def test_provider_failure_propagates_without_retry() -> None:
    fake = FakeLLMProvider(structured_responses=[LLMProviderError("simulated network failure")])
    agent = KnowledgeAgent(llm_provider=fake)

    with pytest.raises(LLMProviderError):
        await agent.answer_question(question="How many leave days?", chunks=_SAMPLE_CHUNKS)

    assert len(fake.calls) == 1  # no retry attempted


async def test_malformed_output_is_retried_once_then_succeeds() -> None:
    fake = FakeLLMProvider(
        structured_responses=[
            InvalidStructuredOutputError("first attempt: bad json"),
            _GROUNDED_ANSWER,
        ]
    )
    agent = KnowledgeAgent(llm_provider=fake)

    outcome = await agent.answer_question(question="How many leave days?", chunks=_SAMPLE_CHUNKS)

    assert outcome.schema == _GROUNDED_ANSWER
    assert len(fake.calls) == 2  # original + one retry


async def test_malformed_output_fails_permanently_after_one_retry() -> None:
    fake = FakeLLMProvider(
        structured_responses=[
            InvalidStructuredOutputError("first attempt: bad json"),
            InvalidStructuredOutputError("second attempt: still bad json"),
        ]
    )
    agent = KnowledgeAgent(llm_provider=fake)

    with pytest.raises(InvalidStructuredOutputError):
        await agent.answer_question(question="How many leave days?", chunks=_SAMPLE_CHUNKS)

    assert len(fake.calls) == 2


async def test_prompt_sent_to_llm_includes_question_and_chunk_content() -> None:
    fake = FakeLLMProvider(structured_responses=[_GROUNDED_ANSWER])
    agent = KnowledgeAgent(llm_provider=fake)

    await agent.answer_question(question="How many leave days do I get?", chunks=_SAMPLE_CHUNKS)

    sent_content = " ".join(m.content for m in fake.calls[0])
    assert "How many leave days do I get?" in sent_content
    assert "Employees accrue 25 days of annual leave per year." in sent_content
    assert str(_CHUNK_ID) in sent_content
