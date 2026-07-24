"""
Agent Registry.

This is what makes "add an agent without modifying Compass" true rather
than aspirational. Agents register themselves against a capability name;
Compass and the Workflow Engine look agents up by that name and never
import a concrete agent class.

Without this registry, Compass's intent router would eventually become a
hardcoded if/elif chain over every agent that ever gets added (Interview
Agent in V2, Analytics Agent in V2, ...). We're building it now, with
zero agents registered, specifically to avoid that.
"""

from app.agents.base import Agent


class AgentRegistry:
    def __init__(self) -> None:
        self._agents: dict[str, Agent] = {}

    def register(self, agent: Agent) -> None:
        if agent.name in self._agents:
            raise ValueError(f"Agent '{agent.name}' is already registered.")
        self._agents[agent.name] = agent

    def get(self, name: str) -> Agent:
        try:
            return self._agents[name]
        except KeyError as exc:
            raise KeyError(
                f"No agent registered for capability '{name}'. "
                f"Available: {sorted(self._agents)}"
            ) from exc

    def list_capabilities(self) -> list[str]:
        return sorted(self._agents)


# Process-wide singleton. Concrete agents call `agent_registry.register(...)`
# at import time once they exist (Slice 4+). Empty in Slice 0 by design.
agent_registry = AgentRegistry()
