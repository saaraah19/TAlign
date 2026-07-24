"""
Workflow Engine — core types.

IMPORTANT DISTINCTION FROM `app/agents/`:

A Workflow is a deterministic sequence of steps (plain Python / business
rules). It is NOT a reasoning agent and must never call an LLM directly.
When a step genuinely requires AI reasoning (e.g. "generate the rejection
email body"), that step declares `requires_agent=True` and names the
agent capability it needs — the WorkflowEngine resolves that capability
via the Agent Registry and invokes it, but the Workflow itself never
constructs a prompt or touches `LLMProvider`.

Example (illustrative only — first real workflow ships in a later slice):

    HireCandidateWorkflow.steps = [
        WorkflowStep("create_employee_record", requires_agent=False),
        WorkflowStep("generate_welcome_email", requires_agent=True,
                     agent_capability="communication.draft_email"),
        WorkflowStep("create_onboarding_checklist", requires_agent=False),
    ]

This keeps the promise from CLAUDE.md: "Business rules remain
deterministic whenever possible" and "[the Workflow Engine] should never
generate business intelligence itself."
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class WorkflowStep:
    name: str
    requires_agent: bool = False
    agent_capability: str | None = None

    def __post_init__(self) -> None:
        if self.requires_agent and not self.agent_capability:
            raise ValueError(
                f"Step '{self.name}' sets requires_agent=True but no "
                f"agent_capability was provided."
            )


@dataclass
class WorkflowRunResult:
    workflow_name: str
    completed_steps: list[str] = field(default_factory=list)
    output: dict[str, Any] = field(default_factory=dict)
    success: bool = True
    error: str | None = None


class Workflow(ABC):
    """
    Base class for every deterministic business workflow.

    Concrete subclasses (e.g. `HireCandidateWorkflow`, later) declare
    `steps` and implement `execute_step`. The engine (see engine.py)
    handles sequencing, agent dispatch, and error handling uniformly so
    individual workflows stay focused on business rules only.
    """

    name: str
    steps: list[WorkflowStep]

    @abstractmethod
    async def execute_step(
        self, step: WorkflowStep, state: dict[str, Any], agent_output: dict[str, Any] | None
    ) -> dict[str, Any]:
        """
        Execute a single deterministic step.

        `agent_output` is populated by the engine when `step.requires_agent`
        is True (the result of the agent it dispatched to); otherwise None.
        Returns a dict merged into the running workflow state.
        """
        raise NotImplementedError
