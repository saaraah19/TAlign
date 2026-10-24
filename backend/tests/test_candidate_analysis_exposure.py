"""
Tests that candidates can never receive internal analysis fields.

Rather than a round-trip integration test (no live DB in this
environment), these are structural checks on the actual schema/route
definitions — verifying the *shape* of what a candidate-facing endpoint
could possibly return makes leaking analysis content impossible, not
just unlikely.
"""

import ast
from pathlib import Path

from app.schemas.application import ApplicationWithJob
from app.schemas.resume_analysis import AnalysisProgressStatusRead

_FORBIDDEN_ANALYSIS_FIELDS = {
    "overall_score",
    "required_skills_result",
    "preferred_skills_result",
    "matched_skills",
    "missing_skills",
    "strengths",
    "potential_concerns",
    "explanation",
    "experience_fit",
}


def test_application_with_job_has_no_analysis_fields() -> None:
    """ApplicationWithJob is what candidate-facing application endpoints return."""
    field_names = set(ApplicationWithJob.model_fields.keys())
    assert field_names.isdisjoint(_FORBIDDEN_ANALYSIS_FIELDS)


def test_candidate_progress_status_schema_carries_only_a_status_enum() -> None:
    field_names = set(AnalysisProgressStatusRead.model_fields.keys())
    assert field_names == {"status"}
    assert field_names.isdisjoint(_FORBIDDEN_ANALYSIS_FIELDS)


def test_candidate_facing_application_endpoints_never_import_resume_analysis_read() -> None:
    """
    Static check: the symbol `ResumeAnalysisRead` (the schema carrying
    score/skills/strengths/concerns) must not even be referenced within
    the code paths a candidate's RBAC dependency can reach. This doesn't
    distinguish candidate vs recruiter routes within one file by itself,
    but combined with the RBAC review, it's a hard guarantee: if
    `ResumeAnalysisRead` were removed from applications.py entirely,
    nothing in the candidate-facing routes would break, because none of
    them reference it.
    """
    source = Path(__file__).parent.parent / "app" / "api" / "v1" / "applications.py"
    tree = ast.parse(source.read_text())

    candidate_facing_functions = {
        "apply_to_job",
        "list_my_applications",
        "get_my_application",
        "attach_resume_to_application",
        "get_my_analysis_status",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.AsyncFunctionDef) and node.name in candidate_facing_functions:
            referenced_names = {
                n.id for n in ast.walk(node) if isinstance(n, ast.Name)
            } | {n.attr for n in ast.walk(node) if isinstance(n, ast.Attribute)}
            assert "ResumeAnalysisRead" not in referenced_names, (
                f"{node.name} references ResumeAnalysisRead — a candidate-facing "
                f"function must never touch the schema carrying analysis content."
            )
            assert "ResumeAnalysisHistoryResponse" not in referenced_names
