"""
KnowledgeAgent.

One method, one LLM call, matching the single-answer-generation shape
of this slice's Knowledge Agent (see prompts.py's module docstring for
why this is the last line of defense, not the only one — structural
citation validation happens one layer up).

Hard boundary, same shape as CommunicationAgent's and
ResumeIntelligenceAgent's: this agent's responsibility ends at
producing a schema-valid answer. It never:
  - performs retrieval itself (it receives an already-retrieved,
    already-company-scoped `list[RetrievedChunk]` — KnowledgeQueryService
    is the caller and the only thing that queries the vector index or
    touches the database)
  - computes confidence (that's confidence.py, driven by retrieval
    similarity scores this agent never sees)
  - validates its own citations against the retrieved set (that's
    KnowledgeQueryService's job, after this agent returns — see
    KnowledgeAnswerValidationError)
"""

from dataclasses import dataclass

from app.agents.knowledge.prompts import (
    KNOWLEDGE_ANSWER_PROMPT_VERSION,
    build_knowledge_answer_prompt,
)
from app.agents.knowledge.schemas import KnowledgeAnswerSchema, RetrievedChunk
from app.agents.shared.structured_output import complete_structured_with_one_retry
from app.core.llm_provider import LLMProvider, get_llm_provider


@dataclass(frozen=True)
class AnswerOutcome:
    schema: KnowledgeAnswerSchema
    llm_provider: str
    llm_model: str
    prompt_version: str


class KnowledgeAgent:
    def __init__(self, llm_provider: LLMProvider | None = None) -> None:
        self._llm = llm_provider or get_llm_provider()

    async def answer_question(
        self,
        *,
        question: str,
        chunks: list[RetrievedChunk],
    ) -> AnswerOutcome:
        """
        Callers must never pass an empty `chunks` list — see
        build_knowledge_answer_prompt's docstring. KnowledgeQueryService
        handles the below-relevance-threshold case as a deterministic
        "no answer" response before this agent is ever invoked.
        """
        messages = build_knowledge_answer_prompt(question=question, chunks=chunks)
        schema = await complete_structured_with_one_retry(
            self._llm, messages, KnowledgeAnswerSchema
        )
        return AnswerOutcome(
            schema=schema,
            llm_provider=self._provider_name(),
            llm_model=self._model_name(),
            prompt_version=KNOWLEDGE_ANSWER_PROMPT_VERSION,
        )

    def _provider_name(self) -> str:
        return type(self._llm).__name__.replace("Provider", "").lower()

    def _model_name(self) -> str:
        return getattr(self._llm, "_default_model", "unknown")
