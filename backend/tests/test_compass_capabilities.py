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


def test_recruiter_can_access_explain_analysis_only() -> None:
    available = compass_capability_registry.available_for_role(Role.RECRUITER)
    names = {c.name for c in available}
    assert names == {"explain_analysis"}


def test_hiring_manager_can_access_explain_analysis() -> None:
    available = compass_capability_registry.available_for_role(Role.HIRING_MANAGER)
    names = {c.name for c in available}
    assert "explain_analysis" in names


def test_admin_can_access_explain_analysis() -> None:
    available = compass_capability_registry.available_for_role(Role.ADMIN)
    names = {c.name for c in available}
    assert "explain_analysis" in names


def test_candidate_cannot_access_explain_analysis() -> None:
    assert compass_capability_registry.get_if_allowed("explain_analysis", Role.CANDIDATE) is None


def test_recruiter_cannot_access_application_status() -> None:
    """application_status is candidate-only — a recruiter asking about "their" status makes no sense."""
    assert compass_capability_registry.get_if_allowed("application_status", Role.RECRUITER) is None


def test_employee_role_has_no_registered_capabilities_in_v1() -> None:
    available = compass_capability_registry.available_for_role(Role.EMPLOYEE)
    assert available == []


def test_compass_resolves_candidate_to_application_status() -> None:
    assert Compass._resolve_capability_for_role(Role.CANDIDATE) == "application_status"


def test_compass_resolves_internal_roles_to_explain_analysis() -> None:
    for role in (Role.ADMIN, Role.RECRUITER, Role.HIRING_MANAGER):
        assert Compass._resolve_capability_for_role(role) == "explain_analysis"


def test_compass_resolves_employee_to_nothing_in_v1() -> None:
    assert Compass._resolve_capability_for_role(Role.EMPLOYEE) is None
