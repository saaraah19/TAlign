"""
Tests for app.agents.knowledge.confidence.confidence_from_similarity.

Zero LLM, zero database — every test just checks the exact band a
given similarity score falls into. Same "the number must be reproducible
and testable in isolation" discipline as test_resume_scoring.py.
"""

from app.agents.knowledge.confidence import (
    CONFIDENCE_ALGORITHM_VERSION,
    MINIMUM_RELEVANCE_THRESHOLD,
    RetrievalConfidence,
    confidence_from_similarity,
)


def test_high_confidence_at_and_above_threshold() -> None:
    assert confidence_from_similarity(0.75) == RetrievalConfidence.HIGH
    assert confidence_from_similarity(0.90) == RetrievalConfidence.HIGH
    assert confidence_from_similarity(1.0) == RetrievalConfidence.HIGH


def test_medium_confidence_band() -> None:
    assert confidence_from_similarity(0.55) == RetrievalConfidence.MEDIUM
    assert confidence_from_similarity(0.65) == RetrievalConfidence.MEDIUM
    assert confidence_from_similarity(0.749) == RetrievalConfidence.MEDIUM


def test_low_confidence_band() -> None:
    assert confidence_from_similarity(0.40) == RetrievalConfidence.LOW
    assert confidence_from_similarity(0.50) == RetrievalConfidence.LOW
    assert confidence_from_similarity(0.549) == RetrievalConfidence.LOW


def test_bands_are_reproducible_for_identical_input() -> None:
    assert confidence_from_similarity(0.6) == confidence_from_similarity(0.6)


def test_algorithm_version_is_set() -> None:
    assert CONFIDENCE_ALGORITHM_VERSION == "similarity_bands_v1"


def test_minimum_relevance_threshold_is_below_low_band() -> None:
    """
    Documents the relationship the module docstring describes: anything
    at/above this threshold gets a real confidence band (starting at
    LOW); anything below it is the caller's responsibility to treat as
    "no relevant chunks," never passed into this function at all.
    """
    assert MINIMUM_RELEVANCE_THRESHOLD == 0.40
    assert confidence_from_similarity(MINIMUM_RELEVANCE_THRESHOLD) == RetrievalConfidence.LOW
