"""
Tests for KnowledgeQueryService: the full RAG pipeline (embed ->
retrieve -> threshold gate -> agent -> confidence). Same mocked-
repository approach as test_application_service_rules.py /
test_communication_service_rules.py — no live database.

Citation-fabrication and cross-tenant scoping get their own dedicated
files (test_knowledge_content_safety.py,
test_knowledge_company_scoping.py) per HANDOVER.md's explicit call for
those to not just inherit confidence from being covered incidentally
here.
"""

import uuid
from unittest.mock import AsyncMock

import pytest

from app.agents.knowledge.agent import AnswerOutcome
from app.agents.knowledge.confidence import CONFIDENCE_ALGORITHM_VERSION, RetrievalConfidence
from app.agents.knowledge.schemas import Citation, KnowledgeAnswerSchema
from app.core.exceptions import AuthorizationError
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


def _make_candidate() -> User:
    return User(
        id=uuid.uuid4(),
        company_id=None,
        account_type=AccountType.CANDIDATE.value,
        email="alex@example.com",
        password_hash="x",
        first_name="Alex",
        last_name="Johnson",
    )


def _make_chunk(*, company_id: uuid.UUID, document_title: str = "Leave Policy") -> KnowledgeChunk:
    document = KnowledgeDocument(
        id=uuid.uuid4(),
        company_id=company_id,
        title=document_title,
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


def _make_service(
    *,
    chunk_repo: AsyncMock,
    agent: AsyncMock,
    embedding_provider: FakeEmbeddingProvider | None = None,
) -> KnowledgeQueryService:
    db = AsyncMock()
    return KnowledgeQueryService(
        db,
        chunk_repository=chunk_repo,
        embedding_provider=embedding_provider or FakeEmbeddingProvider(),
        agent=agent,
    )


async def test_ask_rejects_non_internal_user() -> None:
    service = _make_service(chunk_repo=AsyncMock(), agent=AsyncMock())
    with pytest.raises(AuthorizationError):
        await service.ask(question="How many leave days?", acting_user=_make_candidate())


async def test_ask_returns_no_answer_when_no_chunks_retrieved() -> None:
    company_id = uuid.uuid4()
    chunk_repo = AsyncMock()
    chunk_repo.search_similar.return_value = []
    agent = AsyncMock()
    service = _make_service(chunk_repo=chunk_repo, agent=agent)

    result = await service.ask(
        question="What's the parking policy?", acting_user=_make_recruiter(company_id)
    )

    assert result.grounded is False
    assert result.citations == []
    assert result.confidence is None
    assert result.confidence_algorithm_version == CONFIDENCE_ALGORITHM_VERSION
    agent.answer_question.assert_not_awaited()


async def test_ask_returns_no_answer_when_top_similarity_below_threshold() -> None:
    company_id = uuid.uuid4()
    chunk = _make_chunk(company_id=company_id)
    chunk_repo = AsyncMock()
    chunk_repo.search_similar.return_value = [(chunk, 0.10)]  # well below 0.40 threshold
    agent = AsyncMock()
    service = _make_service(chunk_repo=chunk_repo, agent=agent)

    result = await service.ask(
        question="What's the parking policy?", acting_user=_make_recruiter(company_id)
    )

    assert result.grounded is False
    assert result.confidence is None
    agent.answer_question.assert_not_awaited()


async def test_ask_happy_path_returns_grounded_answer_with_confidence() -> None:
    company_id = uuid.uuid4()
    chunk = _make_chunk(company_id=company_id)
    chunk_repo = AsyncMock()
    chunk_repo.search_similar.return_value = [(chunk, 0.82)]  # HIGH band

    schema = KnowledgeAnswerSchema(
        answer="You accrue 25 days of annual leave per year.",
        citations=[
            Citation(
                document_id=chunk.document_id,
                document_title=chunk.document.title,
                chunk_id=chunk.id,
                excerpt="Employees accrue 25 days of annual leave per year.",
            )
        ],
        grounded=True,
    )
    agent = AsyncMock()
    agent.answer_question.return_value = AnswerOutcome(
        schema=schema, llm_provider="fakellm", llm_model="fake-model", prompt_version="knowledge_answer_v1"
    )
    service = _make_service(chunk_repo=chunk_repo, agent=agent)

    result = await service.ask(
        question="How many leave days do I get?", acting_user=_make_recruiter(company_id)
    )

    assert result.grounded is True
    assert result.confidence == RetrievalConfidence.HIGH
    assert result.citations == schema.citations
    agent.answer_question.assert_awaited_once()
    call_kwargs = agent.answer_question.await_args.kwargs
    assert call_kwargs["question"] == "How many leave days do I get?"
    assert call_kwargs["chunks"][0].chunk_id == chunk.id
    assert call_kwargs["chunks"][0].document_title == "Leave Policy"


async def test_ask_passes_top_k_and_company_id_to_retrieval() -> None:
    company_id = uuid.uuid4()
    chunk_repo = AsyncMock()
    chunk_repo.search_similar.return_value = []
    service = _make_service(chunk_repo=chunk_repo, agent=AsyncMock())

    await service.ask(question="anything", acting_user=_make_recruiter(company_id))

    call_kwargs = chunk_repo.search_similar.await_args.kwargs
    assert call_kwargs["company_id"] == company_id
    assert call_kwargs["top_k"] == 5  # settings.knowledge_retrieval_top_k default
