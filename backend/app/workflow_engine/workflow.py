"""
Workflow Engine — core types.

Revised in Slice 7 from the original Slice-0 scaffold. That scaffold
assumed every AI-backed step would resolve through `agent_registry`
(`WorkflowStep(requires_agent=True, agent_capability="...")`). By the
time Slice 7 actually started, that assumption no longer matched the
codebase: only `ResumeIntelligenceAgent` and `ApplicationStatusAgent`
are registered there. `CommunicationAgent` (and `KnowledgeAgent`) are
deliberately NOT registered — they're plain internal collaborators
owned by their Service (`CommunicationService`, `KnowledgeQueryService`),
and those Services hold real business rules the raw Agent doesn't know
about (e.g. "a drafted email is not yet reviewed, don't treat it as
sent"). Dispatching straight to an Agent via the registry would have
bypassed those rules for exactly the step ("generate_welcome_email")
the original scaffold's own example called out.

So: a `WorkflowStep` no longer names an agent capability at all. It
wraps a single bound async callable — a method on the concrete
`Workflow` subclass — that the engine just calls. If that callable
needs AI reasoning, it's responsible for calling into whichever Service
owns the relevant Agent; the engine itself never touches an Agent, a
Service, Compass, or an LLM provider directly (see
tests/test_workflow_engine_independence.py, which makes this a
mechanically-checked fact).

IMPORTANT DISTINCTION FROM `app/agents/`: a Workflow is a deterministic
sequence of steps (plain Python / business rules). It is NOT a
reasoning agent and must never call an LLM directly — see
HireCandidateWorkflow for the first concrete example.
"""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

#: A step's action receives the workflow's running state dict and
#: returns a dict merged into it. Plain data in, plain data out — no
#: DB session, no Agent, no Compass context.
StepAction = Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]


@dataclass
class WorkflowStep:
    name: str
    action: StepAction


@dataclass
class WorkflowRunResult:
    workflow_name: str
    completed_steps: list[str] = field(default_factory=list)
    output: dict[str, Any] = field(default_factory=dict)
    success: bool = True
    #: Which step raised, if any — None when success is True. Lets a
    #: caller distinguish "everything ran" from "step 2 of 3 failed"
    #: without parsing `error`'s free text.
    failed_step: str | None = None
    error: str | None = None


class Workflow:
    """
    Base class for every deterministic business workflow.

    Concrete subclasses (e.g. `HireCandidateWorkflow`) set `name` and
    build `steps` in their own `__init__` — each step's `action` is
    typically a bound method on that same instance, so it has access to
    whatever context/services the workflow was constructed with without
    the engine needing to know any of that.
    """

    name: str
    steps: list[WorkflowStep]
