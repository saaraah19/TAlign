"""
Structured output schema for the Knowledge Agent.

One LLM call, one schema: retrieved chunks + question in, a grounded
answer out. Mirrors the "one schema per LLM call" shape used by
Communication Agent (DraftEmailSchema) and Resume Intelligence
(ExtractedResumeSchema / AlignmentReasoningSchema) — see those modules'
docstrings for the precedent.

`confidence` is deliberately NOT a field on this schema. Per the
architecture decision (Amendment 3, docs/06_slice6_knowledge_agent.md),
confidence is derived by KnowledgeQueryService purely from the
retrieved chunks' cosine similarity scores, never from the LLM
self-reporting how sure it is — same "the LLM never computes the
number, our own code does" discipline as
app/agents/resume_intelligence/scoring.py and this package's own
confidence.py.

`grounded` exists so the model has an explicit, structurally-required
way to say "the provided chunks don't actually answer this question"
rather than either refusing unhelpfully or quietly drifting into
general knowledge. When `grounded` is False, `citations` MUST be empty
— enforced by a validator below, not just prompt instruction, so a
schema-valid-but-self-contradictory response (grounded=False with
citations attached) can't slip through.

`chunk_id` / `document_id` are typed as `uuid.UUID`, matching
KnowledgeChunk.id / KnowledgeDocument.id exactly (not `str`) — this
lets KnowledgeQueryService validate "every cited chunk_id was actually
in the retrieved set" (see KnowledgeAnswerValidationError in
app/core/exceptions.py) as a direct set-membership check, with no
parse/cast step that could silently coerce a malformed ID into
something that happens to compare equal.
"""

import uuid

from pydantic import BaseModel, Field, model_validator


class RetrievedChunk(BaseModel):
    """
    Plain structured representation of one retrieved chunk, passed into
    the prompt builder and the agent — never the KnowledgeChunk ORM
    model itself. Mirrors the codebase-wide rule that agents receive
    plain structured data, never a DB session or ORM object (see
    CLAUDE.md's engineering principles).

    Deliberately carries only what the LLM needs to answer and cite
    correctly: identifiers to cite (`chunk_id`, `document_id`,
    `document_title`) and the text to reason over (`content`). No
    `company_id`, no embedding vector, no other document's chunks —
    KnowledgeQueryService is responsible for having already scoped and
    ranked the list before it ever reaches here.
    """

    chunk_id: uuid.UUID
    document_id: uuid.UUID
    document_title: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1)


class Citation(BaseModel):
    """
    One retrieved chunk cited as supporting the answer.

    `excerpt` is required (unlike, e.g., SkillMatchResult.evidence in
    the Resume Intelligence schemas, which is optional to accommodate
    a genuine "insufficient evidence" state). There's no equivalent
    legitimate gap here: every Citation names a chunk the model claims
    *does* support the answer, so it must always be able to point to
    the supporting text. If it can't, it shouldn't cite that chunk.
    """

    document_id: uuid.UUID
    document_title: str = Field(min_length=1, max_length=255)
    chunk_id: uuid.UUID
    excerpt: str = Field(
        min_length=1,
        max_length=1000,
        description=(
            "Direct quote or close paraphrase from the chunk's content "
            "that supports the answer — what a human would need to see "
            "to verify this citation without re-reading the whole chunk."
        ),
    )


class KnowledgeAnswerSchema(BaseModel):
    """Output of the Knowledge Agent's single answer-generation call."""

    answer: str = Field(min_length=1)
    citations: list[Citation] = Field(default_factory=list)
    grounded: bool = Field(
        description=(
            "True only if `answer` is actually supported by the provided "
            "chunks. False means the chunks don't answer the question — "
            "`answer` should then explain that plainly rather than "
            "filling the gap from general knowledge, and `citations` "
            "must be empty."
        )
    )

    @model_validator(mode="after")
    def _citations_require_grounding(self) -> "KnowledgeAnswerSchema":
        if not self.grounded and self.citations:
            raise ValueError("citations must be empty when grounded is False")
        return self
