"""
Tests for app.agents.resume_intelligence.scoring.compute_score.

Zero LLM, zero database — every test constructs an AlignmentReasoningSchema
by hand and checks the exact number that comes out. This is what makes
the "reproducible, explainable score" requirement verifiable rather than
just asserted.
"""

from app.agents.resume_intelligence.schemas import (
    AlignmentReasoningSchema,
    ExperienceFitResult,
    SkillMatchResult,
)
from app.agents.resume_intelligence.scoring import SCORING_ALGORITHM_VERSION, compute_score
from app.models.resume_analysis import MatchState


def _reasoning(
    *,
    required: list[MatchState] = (),
    preferred: list[MatchState] = (),
    meets_minimum: bool | None = None,
) -> AlignmentReasoningSchema:
    return AlignmentReasoningSchema(
        required_skills=[
            SkillMatchResult(skill=f"req_{i}", match_state=state)
            for i, state in enumerate(required)
        ],
        preferred_skills=[
            SkillMatchResult(skill=f"pref_{i}", match_state=state)
            for i, state in enumerate(preferred)
        ],
        experience_fit=ExperienceFitResult(meets_minimum=meets_minimum, justification="test"),
        strengths=[],
        potential_concerns=[],
        explanation="test",
    )


def test_all_matched_scores_100() -> None:
    reasoning = _reasoning(
        required=[MatchState.MATCHED, MatchState.MATCHED],
        preferred=[MatchState.MATCHED],
        meets_minimum=True,
    )
    result = compute_score(reasoning, min_years_experience=3)
    assert result.overall_score == 100.0
    assert result.required_skills_score_pct == 100.0
    assert result.preferred_skills_score_pct == 100.0
    assert result.experience_score_pct == 100.0


def test_all_not_matched_scores_0() -> None:
    reasoning = _reasoning(
        required=[MatchState.NOT_MATCHED, MatchState.NOT_MATCHED],
        preferred=[MatchState.NOT_MATCHED],
        meets_minimum=False,
    )
    result = compute_score(reasoning, min_years_experience=3)
    assert result.overall_score == 0.0


def test_insufficient_evidence_scores_half_credit_per_skill() -> None:
    """A single required skill marked insufficient_evidence -> 50% on that dimension."""
    reasoning = _reasoning(required=[MatchState.INSUFFICIENT_EVIDENCE], meets_minimum=None)
    result = compute_score(reasoning, min_years_experience=None)
    assert result.required_skills_score_pct == 50.0


def test_insufficient_evidence_is_not_treated_as_not_matched() -> None:
    """The whole point of the third state: it must score strictly between matched and not_matched."""
    matched = compute_score(
        _reasoning(required=[MatchState.MATCHED]), min_years_experience=None
    ).required_skills_score_pct
    insufficient = compute_score(
        _reasoning(required=[MatchState.INSUFFICIENT_EVIDENCE]), min_years_experience=None
    ).required_skills_score_pct
    not_matched = compute_score(
        _reasoning(required=[MatchState.NOT_MATCHED]), min_years_experience=None
    ).required_skills_score_pct

    assert not_matched < insufficient < matched


def test_experience_insufficient_evidence_scores_50_pct() -> None:
    reasoning = _reasoning(required=[MatchState.MATCHED], meets_minimum=None)
    result = compute_score(reasoning, min_years_experience=5)
    assert result.experience_score_pct == 50.0


def test_missing_preferred_skills_dimension_is_excluded_not_zero() -> None:
    """A job with zero preferred_skills must not silently score that dimension as 0%."""
    reasoning = _reasoning(required=[MatchState.MATCHED], preferred=[], meets_minimum=True)
    result = compute_score(reasoning, min_years_experience=2)
    assert result.preferred_skills_score_pct is None
    # With required=100%, experience=100%, and preferred excluded, overall
    # should be a weighted average of ONLY required+experience, not
    # diluted by treating the missing dimension as 0.
    assert result.overall_score == 100.0


def test_missing_min_years_experience_excludes_experience_dimension() -> None:
    reasoning = _reasoning(required=[MatchState.NOT_MATCHED], meets_minimum=None)
    result = compute_score(reasoning, min_years_experience=None)
    assert result.experience_score_pct is None
    # Only required_skills (0%) remains -> overall should be 0, not
    # averaged with an assumed experience score.
    assert result.overall_score == 0.0


def test_weights_normalize_when_a_dimension_is_excluded() -> None:
    """
    required=100%, preferred=EXCLUDED, experience=0%.
    Weights are required=60, experience=15 (preferred's 25 excluded).
    Expected: (100*60 + 0*15) / (60+15) = 80.0
    """
    reasoning = _reasoning(required=[MatchState.MATCHED], preferred=[], meets_minimum=False)
    result = compute_score(reasoning, min_years_experience=3)
    assert result.overall_score == 80.0


def test_score_is_reproducible_for_identical_input() -> None:
    reasoning = _reasoning(
        required=[MatchState.MATCHED, MatchState.NOT_MATCHED, MatchState.INSUFFICIENT_EVIDENCE],
        preferred=[MatchState.MATCHED],
        meets_minimum=True,
    )
    first = compute_score(reasoning, min_years_experience=4)
    second = compute_score(reasoning, min_years_experience=4)
    assert first == second


def test_matched_and_missing_skill_lists_are_derived_from_same_results_used_for_scoring() -> None:
    reasoning = _reasoning(
        required=[MatchState.MATCHED, MatchState.NOT_MATCHED],
        preferred=[MatchState.MATCHED],
    )
    result = compute_score(reasoning, min_years_experience=None)
    assert set(result.matched_skills) == {"req_0", "pref_0"}
    assert set(result.missing_skills) == {"req_1"}


def test_score_breakdown_carries_the_algorithm_version() -> None:
    reasoning = _reasoning(required=[MatchState.MATCHED])
    result = compute_score(reasoning, min_years_experience=None)
    assert result.algorithm_version == SCORING_ALGORITHM_VERSION == "weighted_v1"


def test_weighted_v1_default_weights_sum_to_100() -> None:
    from app.agents.resume_intelligence.scoring import DEFAULT_WEIGHTS

    assert sum(DEFAULT_WEIGHTS.values()) == 100.0
    assert DEFAULT_WEIGHTS["required_skills"] == 60.0
    assert DEFAULT_WEIGHTS["preferred_skills"] == 25.0
    assert DEFAULT_WEIGHTS["experience"] == 15.0
