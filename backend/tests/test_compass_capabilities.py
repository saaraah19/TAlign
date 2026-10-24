"""
Tests for Compass capability registration (app.compass.capabilities) and
role-based routing (Compass._resolve_capability_for_role).
"""

from app.agents.registry import agent_registry
from app.compass.capabilities import register_default_capabilities
from app.compass.capability_registry import compass_capability_registry
from app.compass.compass import Compass
from app.core.roles import Role


def setup_function() -> None:
    register_default_capabilities()


def test_registration_is_idempotent() -> None:
    register_default_capabilities()
    register_default_capabilities()
    register_default_capabilities()
    # No exception raised (would be ValueError from AgentRegistry.register
    # on a genuine duplicate) — the assertion is that this simply doesn't crash.
    assert "explain_analysis" in agent_registry.list_capabilities()


def test_candidate_can_access_application_status_only() -> None:
    available = compass_capability_registry.available_for_role(Role.CANDIDATE)
    names = {c.name for c in available}
    assert names == {"application_status"}


def test_recruiter_can_access_explain_analysis_and_knowledge_query() -> None:
    available = compass_capability_registry.available_for_role(Role.RECRUITER)
    names = {c.name for c in available}
    assert names == {"explain_analysis", "knowledge_query"}


def test_hiring_manager_can_access_explain_analysis_and_knowledge_query() -> None:
    available = compass_capability_registry.available_for_role(Role.HIRING_MANAGER)
    names = {c.name for c in available}
    assert names == {"explain_analysis", "knowledge_query"}


def test_admin_can_access_explain_analysis_and_knowledge_query() -> None:
    available = compass_capability_registry.available_for_role(Role.ADMIN)
    names = {c.name for c in available}
    assert names == {"explain_analysis", "knowledge_query"}


def test_candidate_cannot_access_explain_analysis() -> None:
    assert compass_capability_registry.get_if_allowed("explain_analysis", Role.CANDIDATE) is None


def test_recruiter_cannot_access_application_status() -> None:
    """application_status is candidate-only — a recruiter asking about "their" status makes no sense."""
    assert compass_capability_registry.get_if_allowed("application_status", Role.RECRUITER) is None


def test_employee_can_access_knowledge_query_only() -> None:
    """
    Added for Sub-slice 9c: the Employee Portal now gives Role.EMPLOYEE
    an actual UI path to knowledge_query (the Knowledge page). Never
    explain_analysis -- that's recruiter-facing candidate-evaluation
    content an employee has no legitimate reason to reach.
    """
    available = compass_capability_registry.available_for_role(Role.EMPLOYEE)
    names = {c.name for c in available}
    assert names == {"knowledge_query"}


def test_compass_resolves_candidate_to_application_status() -> None:
    assert Compass._resolve_capability_for_role(Role.CANDIDATE, "some-workspace-id") == (
        "application_status"
    )
    # Candidates only have one capability regardless of workspace_id.
    assert Compass._resolve_capability_for_role(Role.CANDIDATE, None) == "application_status"


def test_compass_resolves_internal_roles_with_workspace_to_explain_analysis() -> None:
    for role in (Role.ADMIN, Role.RECRUITER, Role.HIRING_MANAGER):
        assert Compass._resolve_capability_for_role(role, "some-application-id") == (
            "explain_analysis"
        )


def test_compass_resolves_internal_roles_without_workspace_to_knowledge_query() -> None:
    for role in (Role.ADMIN, Role.RECRUITER, Role.HIRING_MANAGER):
        assert Compass._resolve_capability_for_role(role, None) == "knowledge_query"


def test_compass_resolves_employee_to_knowledge_query_regardless_of_workspace() -> None:
    """
    Added for Sub-slice 9c: unlike the internal (ADMIN/RECRUITER/
    HIRING_MANAGER) roles above, an employee always resolves to
    knowledge_query even if a workspace_id is somehow present -- they
    should never be routed toward explain_analysis.
    """
    assert Compass._resolve_capability_for_role(Role.EMPLOYEE, None) == "knowledge_query"
    assert (
        Compass._resolve_capability_for_role(Role.EMPLOYEE, "some-workspace-id")
        == "knowledge_query"
    )
