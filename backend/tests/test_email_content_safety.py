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
    build_welcome_email_prompt,
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


def test_welcome_email_prompt_builder_has_no_scoring_parameters() -> None:
    """
    Slice 7 addition: this builder is invoked by the Workflow Engine, not
    a recruiter action, but the same structural guarantee applies
    regardless of trigger source — the signature must physically be
    unable to leak scoring/evaluation data into a "congratulations,
    you're hired" email.
    """
    params = set(inspect.signature(build_welcome_email_prompt).parameters)
    assert params.isdisjoint(_FORBIDDEN_PARAM_NAMES)


def test_welcome_email_prompt_builder_only_allows_name_title_company() -> None:
    params = set(inspect.signature(build_welcome_email_prompt).parameters)
    allowed = {"candidate_first_name", "job_title", "company_name"}
    assert params == allowed


def test_rejection_prompt_builder_only_allows_strengths_from_analysis_data() -> None:
    """
    `strengths` is the one deliberate exception (positive-only flavor
    text) — every other analysis-derived field must be absent.
    """
    params = set(inspect.signature(build_rejection_prompt).parameters)
    allowed = {"candidate_first_name", "job_title", "company_name", "strengths"}
    assert params == allowed
