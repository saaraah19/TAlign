"""
Tests for WorkflowEngine: pure sequencing mechanics, decoupled from any
real Workflow. Uses trivial in-memory step actions (no DB, no
Services) so these tests exercise the engine's own logic in isolation
— HireCandidateWorkflow's actual business behavior is covered
separately in test_hire_candidate_workflow.py.
"""

from typing import Any

import pytest

from app.workflow_engine.engine import WorkflowEngine
from app.workflow_engine.workflow import Workflow, WorkflowStep


class _StubWorkflow(Workflow):
    name = "stub_workflow"

    def __init__(self, steps: list[WorkflowStep]) -> None:
        self.steps = steps


async def _step_ok(state: dict[str, Any]) -> dict[str, Any]:
    return {"step_ran": True}


async def _step_fails(state: dict[str, Any]) -> dict[str, Any]:
    raise RuntimeError("boom")


async def test_successful_workflow_completes_every_step_in_order() -> None:
    calls: list[str] = []

    async def step_a(state: dict[str, Any]) -> dict[str, Any]:
        calls.append("a")
        return {"a": 1}

    async def step_b(state: dict[str, Any]) -> dict[str, Any]:
        calls.append("b")
        assert state["a"] == 1  # proves state flows step-to-step
        return {"b": 2}

    workflow = _StubWorkflow([WorkflowStep("step_a", step_a), WorkflowStep("step_b", step_b)])
    result = await WorkflowEngine().run(workflow)

    assert result.success is True
    assert result.failed_step is None
    assert result.error is None
    assert result.completed_steps == ["step_a", "step_b"]
    assert result.output == {"a": 1, "b": 2}
    assert calls == ["a", "b"]


async def test_failure_at_first_step_stops_immediately() -> None:
    workflow = _StubWorkflow(
        [WorkflowStep("step_one", _step_fails), WorkflowStep("step_two", _step_ok)]
    )
    result = await WorkflowEngine().run(workflow)

    assert result.success is False
    assert result.failed_step == "step_one"
    assert "boom" in result.error
    assert result.completed_steps == []


async def test_failure_at_a_later_step_preserves_partial_completion() -> None:
    """
    Partial-completion tracking: steps that finished before the failure
    must still be recorded, not swallowed by the overall failure.
    """
    workflow = _StubWorkflow(
        [
            WorkflowStep("step_one", _step_ok),
            WorkflowStep("step_two", _step_ok),
            WorkflowStep("step_three", _step_fails),
            WorkflowStep("step_four", _step_ok),
        ]
    )
    result = await WorkflowEngine().run(workflow)

    assert result.success is False
    assert result.failed_step == "step_three"
    assert result.completed_steps == ["step_one", "step_two"]  # step_four never ran


async def test_failure_at_each_individual_step_is_isolated() -> None:
    """
    Parametrized-by-hand: a failure at step N always reports exactly N-1
    completed steps and step N as the failed one, regardless of how many
    steps exist total.
    """
    for failing_index in range(3):
        steps = []
        for i in range(3):
            action = _step_fails if i == failing_index else _step_ok
            steps.append(WorkflowStep(f"step_{i}", action))

        result = await WorkflowEngine().run(_StubWorkflow(steps))

        assert result.success is False
        assert result.failed_step == f"step_{failing_index}"
        assert result.completed_steps == [f"step_{i}" for i in range(failing_index)]


async def test_empty_workflow_succeeds_trivially() -> None:
    result = await WorkflowEngine().run(_StubWorkflow([]))
    assert result.success is True
    assert result.completed_steps == []
    assert result.output == {}


async def test_initial_state_is_available_to_the_first_step() -> None:
    async def reads_initial(state: dict[str, Any]) -> dict[str, Any]:
        return {"seen": state.get("seed")}

    workflow = _StubWorkflow([WorkflowStep("reads_initial", reads_initial)])
    result = await WorkflowEngine().run(workflow, initial_state={"seed": "value"})

    assert result.output["seen"] == "value"
