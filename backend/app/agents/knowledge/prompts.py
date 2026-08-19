"""
Prompt construction for the Knowledge Agent.

Content safety guardrail (structural, not just an instruction): the
single builder function here accepts only `question` and `chunks` —
nothing else. There is no parameter for `company_id`, the full document
list, the asking user's identity, or any other context beyond the
already-scoped-and-ranked chunks KnowledgeQueryService hands it. Same
discipline as Communication Agent's prompts.py: the safest way to
guarantee the wrong thing can't reach the LLM is to make the
prompt-building code physically incapable of receiving it, not to
instruct the model to ignore it. See
tests/test_knowledge_prompt_safety.py for the structural test.

The anti-hallucination instructions below are backed by two independent
layers, matching the "never trust prompt instructions alone" discipline
established elsewhere in this codebase (e.g. Communication Agent's
email content-safety, Resume Intelligence's deterministic scoring):

  1. Prompt instruction (this file): answer only from the provided
     chunks, set `grounded=False` if they don't answer the question.
  2. Structural validation (KnowledgeQueryService, not yet written):
     every `chunk_id` in the returned `citations` is checked against
     the actual set of chunk IDs passed into this prompt. A citation
     naming an unretrieved chunk is a contract violation — raises
     KnowledgeAnswerValidationError — not something the prompt is
     trusted to prevent on its own.

Versioned exactly like the other agents' prompts.py files — bump the
version string whenever prompt text changes meaningfully.
"""

from app.agents.knowledge.schemas import RetrievedChunk
from app.core.llm_provider import LLMMessage

KNOWLEDGE_ANSWER_PROMPT_VERSION = "knowledge_answer_v1"

_GROUNDING_INSTRUCTIONS = """
Answer using ONLY the information in the document chunks provided below. Do
not use any outside knowledge, and do not fill gaps with assumptions or
general knowledge about HR, companies, or policies in general — every claim
in your answer must be traceable to the provided chunks.

If the provided chunks do not contain enough information to answer the
question, do not guess or improvise. Instead, set grounded to false and
write an answer that plainly says the available documents don't cover this,
without inventing a substitute answer.

Every citation you include must reference a chunk_id that was actually given
to you below — never invent or reuse a chunk_id from memory. If grounded is
false, citations must be empty.
""".strip()


def _format_chunk(index: int, chunk: RetrievedChunk) -> str:
    return (
        f"[Chunk {index}]\n"
        f"chunk_id: {chunk.chunk_id}\n"
        f"document_id: {chunk.document_id}\n"
        f"document_title: {chunk.document_title}\n"
        f"content:\n{chunk.content}"
    )


def build_knowledge_answer_prompt(
    *,
    question: str,
    chunks: list[RetrievedChunk],
) -> list[LLMMessage]:
    """
    KnowledgeQueryService is responsible for never calling this with an
    empty `chunks` list — a below-relevance-threshold retrieval is
    handled entirely by the service as a deterministic "no answer"
    response (see confidence.py's module docstring), skipping the LLM
    call altogether rather than asking the model to answer from
    nothing.
    """
    system = LLMMessage(
        role="system",
        content=(
            "You are an HR knowledge assistant answering an employee or "
            "recruiter's question using a company's internal policy documents. "
            "You will be given the question and a set of retrieved document "
            "chunks that may or may not be relevant.\n\n"
            f"{_GROUNDING_INSTRUCTIONS}"
        ),
    )
    formatted_chunks = "\n\n".join(
        _format_chunk(i, chunk) for i, chunk in enumerate(chunks, start=1)
    )
    user = LLMMessage(
        role="user",
        content=(
            f"Question: {question}\n\n"
            f"Retrieved document chunks:\n\n{formatted_chunks}"
        ),
    )
    return [system, user]
