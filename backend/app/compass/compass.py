"""
Compass — the single AI entry point.

Every user of Talign (recruiter, hiring manager, employee, candidate)
talks to Compass and only Compass. No caller in `app/api/` should ever
import a concrete agent or workflow directly — they call `Compass`, and
Compass decides internally whether the request maps to an agent
capability, a Workflow Engine business process (not used in Slice 4 —
no capability needs it yet), or nothing this role can do.

RULE (explicit, from the Slice 2 clarification): Compass never contains
business logic. Its job, exactly:
  - understand intent (here: a role-based heuristic lookup — V1 has one
    capability per role, so there's nothing to disambiguate; see
    `_resolve_capability_for_role`)
  - build context (delegated to CompassContextBuilder, which calls
    existing services — Compass itself never touches a repository or
    the database)
  - check permissions (via the Capability Registry)
  - select the capability (a name lookup)
  - route the request (call `agent.run(...)`, return its output)

Every actual decision — what the analysis says, what the candidate's
status is, whether a transition is legal — was already made elsewhere
(a domain service, or an LLM call inside an Agent) before Compass ever
sees it. Compass only ever moves data and picks which Agent gets to see
which slice of it.

Not a module-level singleton (unlike Slice 0's original sketch): Compass
needs a request-scoped DB session, same as every *Service class in this
codebase — constructed fresh per request (`Compass(db)`), never reused
across requests.
"""

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base import AgentContext
from app.agents.registry import AgentRegistry, agent_registry
from app.compass.capability_registry import CompassCapabilityRegistry, compass_capability_registry
from app.compass.context import WorkspaceContext
from app.compass.context_builder import CompassContextBuilder
from app.core.exceptions import NotFoundError
from app.core.roles import Role


@dataclass
class CompassResponse:
    message: str
    capability_used: str | None
    reasoning: str | None = None


class Compass:
    def __init__(
        self,
        db: AsyncSession,
        agent_registry_: AgentRegistry = agent_registry,
        capability_registry: CompassCapabilityRegistry = compass_capability_registry,
    ) -> None:
        self._agents = agent_registry_
        self._capabilities = capability_registry
        self._context_builder = CompassContextBuilder(db)

    async def handle_message(self, message: str, context: WorkspaceContext) -> CompassResponse:
        capability_name = self._resolve_capability_for_role(context.role)
        if capability_name is None:
            return CompassResponse(
                message="I'm not able to help with that yet.", capability_used=None
            )

        capability = self._capabilities.get_if_allowed(capability_name, context.role)
        if capability is None:
            # Defense in depth: _resolve_capability_for_role already only
            # returns names valid for this role, so this branch should be
            # unreachable in practice — but Compass never assumes its own
            # internal consistency is a substitute for checking.
            return CompassResponse(
                message="You don't have access to that capability.", capability_used=None
            )

        if context.workspace_id is None:
            return CompassResponse(
                message="I need to know which application you're asking about.",
                capability_used=None,
            )

        try:
            payload = await self._build_context_payload(capability_name, message, context)
        except NotFoundError:
            return CompassResponse(
                message="I couldn't find that application.", capability_used=None
            )

        agent = self._agents.get(capability_name)
        result = await agent.run(
            AgentContext(company_id=context.company_id, user_id=context.user_id, payload=payload)
        )
        return CompassResponse(
            message=result.output["message"],
            capability_used=capability_name,
            reasoning=result.reasoning,
        )

    @staticmethod
    def _resolve_capability_for_role(role: Role) -> str | None:
        """
        V1 heuristic: exactly one capability per role, so there is
        nothing to disambiguate from the message text — routing is a
        role lookup, not intent classification. Real (LLM-based) intent
        recognition is worth building once there are enough capabilities
        that this stops being true; see docs/04_slice4_resume_intelligence.md
        section E.
        """
        if role is Role.CANDIDATE:
            return "application_status"
        if role in (Role.ADMIN, Role.RECRUITER, Role.HIRING_MANAGER):
            return "explain_analysis"
        return None

    async def _build_context_payload(
        self, capability_name: str, message: str, context: WorkspaceContext
    ) -> dict:
        application_id = uuid.UUID(context.workspace_id)

        if capability_name == "application_status":
            return await self._context_builder.build_for_application_status(
                application_id=application_id, candidate=context.data["current_user"]
            )
        if capability_name == "explain_analysis":
            return await self._context_builder.build_for_explain_analysis(
                application_id=application_id,
                acting_user=context.data["current_user"],
                question=message,
                role=context.role,
            )
        raise ValueError(f"No context builder wired for capability '{capability_name}'.")
