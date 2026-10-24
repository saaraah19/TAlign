"""
Base Agent interface.

An "agent" in Talign is a specialized, LLM-backed reasoning unit with ONE
job (e.g. Resume Intelligence, Knowledge / RAG, Communication drafting).

Hard boundaries, enforced by convention here and by review, not just docs:
  - Agents never talk to end users directly. Only Compass and the
    Workflow Engine invoke agents.
  - Agents never perform deterministic business logic (that belongs in
    `app/services/` or `app/workflow_engine/`). If a step doesn't need
    the LLM, it doesn't belong in an agent.
  - Agents depend on `LLMProvider` (see app/core/llm_provider.py) via
    constructor injection — never a concrete SDK.

No concrete agent exists in Slice 0. This file defines the shape so the
first real agent (Resume Intelligence, later) has a contract to satisfy
rather than inventing its own pattern.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class AgentContext:
    """
    The subset of WorkspaceContext (see app/compass/context.py) relevant
    to a single agent invocation. Agents receive only what they need,
    not the full shared context object — keeps agents testable in
    isolation without constructing an entire workspace.
    """

    company_id: str
    user_id: str
    payload: dict[str, Any]


@dataclass
class AgentResult:
    """
    Uniform result envelope every agent returns.

    `reasoning` is mandatory-by-convention (not enforced by the type
    system in Slice 0) because every AI recommendation in Talign must be
    explainable — see CLAUDE.md AI Principles.
    """

    output: dict[str, Any]
    reasoning: str
    confidence: float | None = None


class Agent(ABC):
    """Every specialized agent (Resume, Knowledge, Communication...) implements this."""

    #: Unique capability name used by the Agent Registry and by Compass's
    #: intent → capability routing. e.g. "resume.analyze", "knowledge.query"
    name: str

    @abstractmethod
    async def run(self, context: AgentContext) -> AgentResult:
        """Execute the agent's single responsibility and return a result."""
        raise NotImplementedError
