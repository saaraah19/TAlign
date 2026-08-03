"""
Content safety guardrail test — structural, not a convention.

Verifies that neither prompt builder even has a parameter through which
score/missing_skills/potential_concerns/match_state could reach the
LLM. This is checked against the actual function signature rather than
just documented, matching the same philosophy already used in
tests/test_candidate_analysis_exposure.py: the safest guarantee is
"the code physically cannot do this," not "the code is instructed not
to."
"""

import inspect

from app.agents.communication.prompts import (
    build_interview_invitation_prompt,
    build_rejection_prompt,
)

_FORBIDDEN_PARAM_NAMES = {
    "score",
    "overall_score",
    "missing_skills",
    "potential_concerns",
    "match_state",
    "required_skills_result",
    "preferred_skills_result",
    "experience_fit",
}


def test_rejection_prompt_builder_has_no_scoring_parameters() -> None:
    params = set(inspect.signature(build_rejection_prompt).parameters)
    assert params.isdisjoint(_FORBIDDEN_PARAM_NAMES)


def test_interview_invitation_prompt_builder_has_no_scoring_parameters() -> None:
    params = set(inspect.signature(build_interview_invitation_prompt).parameters)
    assert params.isdisjoint(_FORBIDDEN_PARAM_NAMES)


def test_rejection_prompt_builder_only_allows_strengths_from_analysis_data() -> None:
    """
    `strengths` is the one deliberate exception (positive-only flavor
    text) — every other analysis-derived field must be absent.
    """
    params = set(inspect.signature(build_rejection_prompt).parameters)
    allowed = {"candidate_first_name", "job_title", "company_name", "strengths"}
    assert params == allowed
