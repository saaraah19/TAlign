"""
Alignment scoring.

This file contains ZERO LLM calls. It exists specifically so the
"reproducible, explainable score" requirement is a mechanical fact:
given the same AlignmentReasoningSchema and the same Job requirements,
`compute_score` always returns the same number, and every test in
tests/test_resume_scoring.py exercises this function directly with
synthetic input — no model, no network, no randomness.

SCORING_ALGORITHM_VERSION: bump this any time the formula below changes.
Persisted on every ResumeAnalysis row (scoring_algorithm_version) so a
historical analysis's score can always be traced back to the exact
arithmetic that produced it, even after the formula changes later.

--- Methodology ---

Three dimensions, weighted:

    required_skills:   60%
    preferred_skills:  25%
    experience:         15%

Per-skill scoring (required and preferred use the same rule):
    MATCHED               -> 1.0 point
    INSUFFICIENT_EVIDENCE -> 0.5 point   (see "insufficient evidence" below)
    NOT_MATCHED            -> 0.0 point

A dimension's percentage = (sum of points / number of skills) * 100.
If a job defines zero skills for a dimension (e.g. no preferred_skills
were entered), that dimension is EXCLUDED — not scored as 0.

Experience dimension:
    meets_minimum = True   -> 100%
    meets_minimum = False  -> 0%
    meets_minimum = None (insufficient evidence) -> 50%   (same "half
        credit for uncertainty" rule as skills, for consistency)
    job.min_years_experience is None -> dimension EXCLUDED entirely
        (there was no requirement to evaluate against)

--- Insufficient evidence: exactly how it affects the score ---

"Insufficient evidence" is NOT "not matched" and is NOT "matched" — it's
a distinct, honest third state acknowledging the resume didn't provide
enough information either way (see the model docstring in
app/models/resume_analysis.py for why this matters for fairness). It is
scored as HALF credit (0.5 of a point per skill, 50% for the experience
dimension) — a deliberate middle value: it does not penalize the
candidate as if the skill were confirmed absent, and it does not reward
them as if it were confirmed present. This is a value judgment, not a
mathematical necessity — it is documented here explicitly, versioned via
SCORING_ALGORITHM_VERSION, and open to revision (e.g., a future version
might weight it differently) but never silently.

--- Weight normalization when a dimension is excluded ---

If any dimension is excluded, remaining weights are normalized
proportionally rather than the excluded dimension simply being dropped
(which would silently change what "100" means). The formula:

    overall = sum(pct_i * weight_i for included dimensions)
              / sum(weight_i for included dimensions)

Since each pct_i is already 0-100 and weights sum to 100 when nothing is
excluded, this reduces to the plain weighted average in the normal case,
and correctly redistributes weight proportionally when a dimension is
missing (dividing by the sum of INCLUDED weights, not always 100).
"""

from dataclasses import dataclass

from app.agents.resume_intelligence.schemas import AlignmentReasoningSchema, SkillMatchResult
from app.models.resume_analysis import MatchState

SCORING_ALGORITHM_VERSION = "weighted_v1"

DEFAULT_WEIGHTS = {
    "required_skills": 60.0,
    "preferred_skills": 25.0,
    "experience": 15.0,
}

_MATCH_STATE_POINTS = {
    MatchState.MATCHED: 1.0,
    MatchState.INSUFFICIENT_EVIDENCE: 0.5,
    MatchState.NOT_MATCHED: 0.0,
}

_EXPERIENCE_MEETS_MINIMUM_POINTS = {
    True: 100.0,
    False: 0.0,
    None: 50.0,  # insufficient evidence — see module docstring
}


@dataclass(frozen=True)
class ScoreBreakdown:
    overall_score: float
    required_skills_score_pct: float | None
    preferred_skills_score_pct: float | None
    experience_score_pct: float | None
    matched_skills: list[str]
    missing_skills: list[str]
    algorithm_version: str = SCORING_ALGORITHM_VERSION


def _skill_dimension_pct(results: list[SkillMatchResult]) -> float | None:
    """Returns None (dimension excluded) if there are no skills to evaluate."""
    if not results:
        return None
    total_points = sum(_MATCH_STATE_POINTS[r.match_state] for r in results)
    return (total_points / len(results)) * 100.0


def compute_score(
    reasoning: AlignmentReasoningSchema,
    *,
    min_years_experience: int | None,
    weights: dict[str, float] | None = None,
) -> ScoreBreakdown:
    """
    Pure function: structured LLM judgments + job requirements ->
    reproducible score. Called by ResumeAnalysisService after the
    agent's alignment-reasoning LLM call returns — never by the agent
    itself (see agent.py's module docstring: "the agent's responsibility
    ends at producing structured intelligence").
    """
    w = weights or DEFAULT_WEIGHTS

    required_pct = _skill_dimension_pct(reasoning.required_skills)
    preferred_pct = _skill_dimension_pct(reasoning.preferred_skills)

    experience_pct: float | None
    if min_years_experience is None:
        experience_pct = None  # no requirement was set -> dimension excluded
    else:
        experience_pct = _EXPERIENCE_MEETS_MINIMUM_POINTS[reasoning.experience_fit.meets_minimum]

    dimensions = [
        ("required_skills", w["required_skills"], required_pct),
        ("preferred_skills", w["preferred_skills"], preferred_pct),
        ("experience", w["experience"], experience_pct),
    ]
    included = [(name, weight, pct) for name, weight, pct in dimensions if pct is not None]

    if not included:
        # No dimension had anything to evaluate — shouldn't happen in
        # practice (required_skills should always be non-empty for a
        # real job), but fail loudly with 0 rather than divide by zero.
        overall = 0.0
    else:
        weighted_sum = sum(pct * weight for _, weight, pct in included)
        total_weight = sum(weight for _, weight, _ in included)
        overall = weighted_sum / total_weight

    matched_skills = [
        r.skill
        for r in (*reasoning.required_skills, *reasoning.preferred_skills)
        if r.match_state == MatchState.MATCHED
    ]
    missing_skills = [
        r.skill
        for r in (*reasoning.required_skills, *reasoning.preferred_skills)
        if r.match_state == MatchState.NOT_MATCHED
    ]

    return ScoreBreakdown(
        overall_score=round(overall, 1),
        required_skills_score_pct=required_pct,
        preferred_skills_score_pct=preferred_pct,
        experience_score_pct=experience_pct,
        matched_skills=matched_skills,
        missing_skills=missing_skills,
    )
