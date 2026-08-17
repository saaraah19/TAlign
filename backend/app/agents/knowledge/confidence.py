"""
Retrieval confidence.

This file contains ZERO LLM calls, by explicit product decision:
confidence in a knowledge answer is derived from how well the retrieved
chunks actually matched the question (a measurable, reproducible fact
about the vector search), never from the LLM self-reporting how sure it
feels — a model asked "how confident are you" is notoriously unreliable
at that specific task and its answer isn't grounded in anything real.
Same "the LLM never computes the number, our own code does" philosophy
as app/agents/resume_intelligence/scoring.py.

CONFIDENCE_ALGORITHM_VERSION: bump any time the thresholds below change.
Not currently persisted anywhere (confidence is computed fresh per
query, not stored per-document like ResumeAnalysis's score is), but
versioned regardless so a future change to the thresholds is a
deliberate, documented step rather than a silent behavior shift.

--- Methodology ---

Confidence is derived from the TOP retrieved chunk's cosine similarity
score only (not an average across the retrieved set) — the top chunk is
the most direct signal of whether genuinely relevant content was found
at all; averaging in weaker lower-ranked chunks would dilute that
signal for no benefit.

Four bands, using cosine similarity (1.0 = identical, 0.0 = unrelated):

    similarity < MINIMUM_RELEVANCE_THRESHOLD (0.40)
        -> not a confidence level at all. KnowledgeQueryService treats
           this as "no relevant chunks found" and skips the LLM call
           entirely — see that service's module docstring.

    0.40 <= similarity < 0.55  -> LOW
    0.55 <= similarity < 0.75  -> MEDIUM
    similarity >= 0.75         -> HIGH

These thresholds are explicitly starting defaults, not claimed-optimal
numbers — see docs/06_slice6_knowledge_agent.md's evaluation strategy
section. They're expected to be tuned once a real evaluation set (real
HR documents, real questions) exists; changing them is a one-line edit
here, with the version bump making the change traceable.
"""

from enum import StrEnum

CONFIDENCE_ALGORITHM_VERSION = "similarity_bands_v1"

MINIMUM_RELEVANCE_THRESHOLD = 0.40
_MEDIUM_THRESHOLD = 0.55
_HIGH_THRESHOLD = 0.75


class RetrievalConfidence(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


def confidence_from_similarity(top_similarity: float) -> RetrievalConfidence:
    """
    Callers must check `top_similarity >= MINIMUM_RELEVANCE_THRESHOLD`
    themselves before calling this — see KnowledgeQueryService, which
    never calls this function at all for a below-threshold top result
    (that's a "no answer" case, not a LOW-confidence answer).
    """
    if top_similarity >= _HIGH_THRESHOLD:
        return RetrievalConfidence.HIGH
    if top_similarity >= _MEDIUM_THRESHOLD:
        return RetrievalConfidence.MEDIUM
    return RetrievalConfidence.LOW
