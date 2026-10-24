"""
Compass Capability Registry.

Role-awareness is implemented here, not by filtering AI output after the
fact. A capability that a role cannot access is simply not resolvable for
that role — Compass never constructs a prompt or calls an agent for it.

This is why a Candidate's Compass literally cannot "explain alignment
score": that capability is never registered against Role.CANDIDATE, so
intent recognition for a candidate session will never route to it,
regardless of how the question is phrased.

Empty in Slice 0 — populated as real capabilities (backed by real agents
or workflows) ship in later slices.
"""

from dataclasses import dataclass

from app.core.roles import Role


@dataclass(frozen=True)
class CompassCapability:
    #: Matches an Agent.name (app/agents/base.py) or a Workflow.name
    #: (app/workflow_engine/workflow.py) — Compass doesn't care which,
    #: it just needs a resolvable identifier.
    name: str
    description: str
    allowed_roles: frozenset[Role]

    def is_allowed_for(self, role: Role) -> bool:
        return role in self.allowed_roles


class CompassCapabilityRegistry:
    def __init__(self) -> None:
        self._capabilities: dict[str, CompassCapability] = {}

    def register(self, capability: CompassCapability) -> None:
        if capability.name in self._capabilities:
            raise ValueError(f"Capability '{capability.name}' is already registered.")
        self._capabilities[capability.name] = capability

    def available_for_role(self, role: Role) -> list[CompassCapability]:
        return [cap for cap in self._capabilities.values() if cap.is_allowed_for(role)]

    def get_if_allowed(self, name: str, role: Role) -> CompassCapability | None:
        capability = self._capabilities.get(name)
        if capability is None or not capability.is_allowed_for(role):
            return None
        return capability


# Process-wide singleton, mirroring the Agent Registry pattern.
compass_capability_registry = CompassCapabilityRegistry()
