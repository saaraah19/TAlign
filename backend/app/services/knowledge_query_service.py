"""
KnowledgeQueryService.

The actual RAG pipeline. Owns the full flow Compass's `knowledge_query`
capability delegates to (see app/compass/capabilities.py and
context_builder.py — Compass itself never touches retrieval, embeddings,
or the agent directly, per the "Compass is a pure router" rule):

    embed the question
    -> retrieve top-k chunks for this company only
    -> below MINIMUM_RELEVANCE_THRESHOLD? deterministic "no answer",
       skip the LLM call entirely (anti-hallucination by construction,
       not by instruction — see confidence.py's module docstring)
    -> otherwise call KnowledgeAgent.answer_question()
    -> validate every returned citation's chunk_id was actually in the
       retrieved set (KnowledgeAnswerValidationError if not — a
       schema-valid response whose *content* fabricated a source)
    -> compute confidence from the top chunk's similarity
       (confidence.py — never from the LLM)
    -> return a combined result

SECURITY: retrieval always goes through
KnowledgeChunkRepository.search_similar, which filters by `company_id`
as its first WHERE condition (see that repository's module docstring).
This service never queries chunks any other way — no bypass path exists
for a request to see another company's documents. See
tests/test_knowledge_company_scoping.py.
"""

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.knowledge.agent import KnowledgeAgent
from app.agents.knowledge.confidence import (
    CONFIDENCE_ALGORITHM_VERSION,
    MINIMUM_RELEVANCE_THRESHOLD,
    RetrievalConfidence,
    confidence_from_similarity,
)
from app.agents.knowledge.schemas import Citation, RetrievedChunk
from app.core.config import settings
from app.core.exceptions import AuthorizationError, KnowledgeAnswerValidationError
from app.core.llm_provider import EmbeddingProvider, get_embedding_provider
from app.models.user import User
from app.repositories.knowledge_chunk_repository import KnowledgeChunkRepository

_NO_ANSWER_TEXT = (
    "I don't have information about that in the company's knowledge base. "
    "You may want to check with your HR team directly, or upload the relevant "
    "document if one exists."
)


@dataclass(frozen=True)
class KnowledgeQueryResult:
    answer: str
    citations: list[Citation]
    grounded: bool
    confidence: RetrievalConfidence | None  # None only for the deterministic "no answer" case
    confidence_algorithm_version: str


class KnowledgeQueryService:
    def __init__(
        self,
        db: AsyncSession,
        chunk_repository: KnowledgeChunkRepository | None = None,
        embedding_provider: EmbeddingProvider | None = None,
        agent: KnowledgeAgent | None = None,
    ) -> None:
        self._db = db
        self._chunks = chunk_repository or KnowledgeChunkRepository(db)
        self._embeddings = embedding_provider or get_embedding_provider()
        self._agent = agent or KnowledgeAgent()

    async def ask(self, *, question: str, acting_user: User) -> KnowledgeQueryResult:
        self._assert_internal_with_company(acting_user)
        assert acting_user.company_id is not None  # guaranteed by the assertion above

        query_vector = await self._embeddings.embed_query(question)
        retrieved = await self._chunks.search_similar(
            company_id=acting_user.company_id,
            query_embedding=query_vector,
            top_k=settings.knowledge_retrieval_top_k,
        )

        if not retrieved or retrieved[0][1] < MINIMUM_RELEVANCE_THRESHOLD:
            # Deterministic "no answer" — no LLM call at all. This is the
            # anti-hallucination guarantee confidence.py's docstring
            # describes: a below-threshold top match is treated as "no
            # relevant chunks found", never handed to the LLM to attempt
            # anyway.
            return KnowledgeQueryResult(
                answer=_NO_ANSWER_TEXT,
                citations=[],
                grounded=False,
                confidence=None,
                confidence_algorithm_version=CONFIDENCE_ALGORITHM_VERSION,
            )

        retrieved_chunk_ids = {chunk.id for chunk, _similarity in retrieved}
        prompt_chunks = [
            RetrievedChunk(
                chunk_id=chunk.id,
                document_id=chunk.document_id,
                document_title=chunk.document.title,
                content=chunk.content,
            )
            for chunk, _similarity in retrieved
        ]

        outcome = await self._agent.answer_question(question=question, chunks=prompt_chunks)
        answer = outcome.schema

        self._validate_citations(answer.citations, retrieved_chunk_ids)

        top_similarity = retrieved[0][1]
        confidence = confidence_from_similarity(top_similarity)

        return KnowledgeQueryResult(
            answer=answer.answer,
            citations=answer.citations,
            grounded=answer.grounded,
            confidence=confidence,
            confidence_algorithm_version=CONFIDENCE_ALGORITHM_VERSION,
        )

    @staticmethod
    def _validate_citations(citations: list[Citation], retrieved_chunk_ids: set[uuid.UUID]) -> None:
        """
        Structural anti-hallucination check (see module docstring and
        KnowledgeAnswerValidationError's docstring). Every citation's
        chunk_id must be a member of the set actually retrieved and
        passed into the prompt — anything else is the model fabricating
        a source, not merely a formatting slip, so this raises rather
        than silently dropping the bad citation.
        """
        for citation in citations:
            if citation.chunk_id not in retrieved_chunk_ids:
                raise KnowledgeAnswerValidationError(
                    f"Answer cited chunk_id {citation.chunk_id}, which was not among "
                    "the retrieved chunks provided to the model."
                )

    @staticmethod
    def _assert_internal_with_company(user: User) -> None:
        # Defensive check: RBAC at the API layer (Compass capability
        # scoping — ADMIN/RECRUITER/HIRING_MANAGER only, see
        # app/compass/capabilities.py) already restricts who can reach
        # this, but a service should never trust that a caller enforced
        # its own preconditions correctly.
        if user.company_id is None:
            raise AuthorizationError("This action requires an internal company account.")
