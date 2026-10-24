"""
Structural anti-hallucination test for the Knowledge Agent's RAG
pipeline — dedicated file, not folded into test_knowledge_query_service.py,
per HANDOVER.md's explicit instruction: a response citing an unretrieved
chunk_id is a severity tier of its own (KnowledgeAnswerValidationError,
distinct from a plain schema-shape failure) and deserves a test that
can't be missed or accidentally deleted alongside general pipeline
tests. Mirrors test_email_content_safety.py's spirit — this is the
"physically cannot" guarantee for RAG grounding, not just "currently
doesn't fabricate a source".
"""

import uuid
from unittest.mock import AsyncMock

import pytest

from app.agents.knowledge.agent import AnswerOutcome
from app.agents.knowledge.schemas import Citation, KnowledgeAnswerSchema
from app.core.exceptions import KnowledgeAnswerValidationError
from app.core.roles import AccountType
from app.models.knowledge_chunk import KnowledgeChunk
from app.models.knowledge_document import KnowledgeDocument
from app.models.user import User
from app.services.knowledge_query_service import KnowledgeQueryService
from tests.fakes import FakeEmbeddingProvider


def _make_recruiter(company_id: uuid.UUID) -> User:
    return User(
        id=uuid.uuid4(),
        company_id=company_id,
        account_type=AccountType.INTERNAL.value,
        email="emma@example.com",
        password_hash="x",
        first_name="Emma",
        last_name="Martin",
    )


def _make_retrieved_chunk(company_id: uuid.UUID) -> KnowledgeChunk:
    document = KnowledgeDocument(
        id=uuid.uuid4(),
        company_id=company_id,
        title="Leave Policy",
        category="policy",
        file_path="/tmp/x.txt",
        original_filename="x.txt",
        content_type="text/plain",
        file_size_bytes=10,
        status="ready",
    )
    chunk = KnowledgeChunk(
        id=uuid.uuid4(),
        document_id=document.id,
        company_id=company_id,
        chunk_index=0,
        content="Employees accrue 25 days of annual leave per year.",
        token_count=8,
    )
    chunk.document = document
    return chunk


async def test_citation_referencing_unretrieved_chunk_is_rejected() -> None:
    """
    The model returns a schema-VALID answer whose citation names a
    chunk_id that was never in the retrieved/prompted set (e.g.
    invented, or carried over from a different question's context).
    This must raise KnowledgeAnswerValidationError — the answer is not
    silently accepted with a bad citation dropped, and it is not
    returned to the user at all.
    """
    company_id = uuid.uuid4()
    retrieved_chunk = _make_retrieved_chunk(company_id)
    fabricated_chunk_id = uuid.uuid4()  # deliberately NOT retrieved_chunk.id

    chunk_repo = AsyncMock()
    chunk_repo.search_similar.return_value = [(retrieved_chunk, 0.9)]

    schema = KnowledgeAnswerSchema(
        answer="You accrue 25 days of annual leave per year.",
        citations=[
            Citation(
                document_id=retrieved_chunk.document_id,
                document_title="Leave Policy",
                chunk_id=fabricated_chunk_id,
                excerpt="Employees accrue 25 days of annual leave per year.",
            )
        ],
        grounded=True,
    )
    agent = AsyncMock()
    agent.answer_question.return_value = AnswerOutcome(
        schema=schema,
        llm_provider="fakellm",
        llm_model="fake-model",
        prompt_version="knowledge_answer_v1",
    )

    db = AsyncMock()
    service = KnowledgeQueryService(
        db, chunk_repository=chunk_repo, embedding_provider=FakeEmbeddingProvider(), agent=agent
    )

    with pytest.raises(KnowledgeAnswerValidationError):
        await service.ask(
            question="How many leave days do I get?", acting_user=_make_recruiter(company_id)
        )


async def test_citation_referencing_retrieved_chunk_is_accepted() -> None:
    """Control case: a citation that DOES match a retrieved chunk_id must pass through untouched."""
    company_id = uuid.uuid4()
    retrieved_chunk = _make_retrieved_chunk(company_id)

    chunk_repo = AsyncMock()
    chunk_repo.search_similar.return_value = [(retrieved_chunk, 0.9)]

    schema = KnowledgeAnswerSchema(
        answer="You accrue 25 days of annual leave per year.",
        citations=[
            Citation(
                document_id=retrieved_chunk.document_id,
                document_title="Leave Policy",
                chunk_id=retrieved_chunk.id,
                excerpt="Employees accrue 25 days of annual leave per year.",
            )
        ],
        grounded=True,
    )
    agent = AsyncMock()
    agent.answer_question.return_value = AnswerOutcome(
        schema=schema,
        llm_provider="fakellm",
        llm_model="fake-model",
        prompt_version="knowledge_answer_v1",
    )

    db = AsyncMock()
    service = KnowledgeQueryService(
        db, chunk_repository=chunk_repo, embedding_provider=FakeEmbeddingProvider(), agent=agent
    )

    result = await service.ask(
        question="How many leave days do I get?", acting_user=_make_recruiter(company_id)
    )
    assert result.citations[0].chunk_id == retrieved_chunk.id
