"""
Default capability registration.

Called once from app.main's lifespan startup. Registers each concrete
Agent in the Agent Registry (app.agents.registry) and its allowed roles
in the Compass Capability Registry (app.compass.capability_registry).

This is the file that gets a new few lines whenever a capability is
added — Compass itself (compass.py) never changes. That's the
"extensible without rewriting Compass" requirement, made concrete: a V2
Interview Agent capability is one new CompassCapability registration
and one new agent_registry.register() call here, nothing else.
"""

from app.agents.application_status.agent import ApplicationStatusAgent
from app.agents.registry import agent_registry
from app.agents.resume_intelligence.agent import ResumeIntelligenceAgent
from app.compass.capability_registry import CompassCapability, compass_capability_registry
from app.core.roles import Role


def register_default_capabilities() -> None:
    """
    Idempotent — safe to call more than once (e.g. across multiple app
    startups within one test session, since agent_registry and
    compass_capability_registry are process-wide module singletons, not
    reset between calls). Registering twice would otherwise raise
    ValueError from AgentRegistry.register's duplicate-name guard.
    """
    if "explain_analysis" not in agent_registry.list_capabilities():
        agent_registry.register(ApplicationStatusAgent())
        agent_registry.register(ResumeIntelligenceAgent())

    if compass_capability_registry.get_if_allowed("application_status", Role.CANDIDATE) is None:
        compass_capability_registry.register(
            CompassCapability(
                name="application_status",
                description=(
                    "Tells a candidate the current pipeline stage of one of their applications."
                ),
                allowed_roles=frozenset({Role.CANDIDATE}),
            )
        )
        compass_capability_registry.register(
            CompassCapability(
                name="explain_analysis",
                description=(
                    "Answers a recruiter/hiring manager's question about an existing "
                    "Resume Intelligence alignment analysis, grounded strictly in the "
                    "stored analysis — never introduces new judgments or a new score."
                ),
                allowed_roles=frozenset({Role.ADMIN, Role.RECRUITER, Role.HIRING_MANAGER}),
            )
        )
        compass_capability_registry.register(
            CompassCapability(
                name="knowledge_query",
                description=(
                    "Answers a general company-knowledge question (policies, benefits, "
                    "procedures) via retrieval-augmented generation over uploaded "
                    "Knowledge Documents. Not workspace-scoped — unlike explain_analysis, "
                    "it isn't about any specific application. Role scope deliberately "
                    "excludes Role.EMPLOYEE: the Employee Portal is V2-deferred, so "
                    "employees have no UI path to reach this capability yet, and granting "
                    "a role a capability with zero way to invoke it is dead RBAC surface "
                    "(see HANDOVER.md's Slice 6 architecture notes)."
                ),
                allowed_roles=frozenset({Role.ADMIN, Role.RECRUITER, Role.HIRING_MANAGER}),
            )
        )
