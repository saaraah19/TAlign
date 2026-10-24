"""
Workflow Engine runner.

Owns sequencing only — walks `workflow.steps` in order, calls each
step's bound `action` with the running state dict, merges the result
back into state. Nothing else. It does not know about hiring,
onboarding, Agents, Services, Compass, the database, or any specific
business process — all of that lives in the concrete `Workflow`
subclass and whatever it was constructed with.

No retry logic: the first step to raise stops the run immediately.
Steps already completed stay recorded in `result.completed_steps` (and
`result.failed_step` names the one that didn't) — this is what makes
partial-completion genuinely observable rather than an all-or-nothing
black box, per Slice 7's explicit requirement.
"""

from typing import Any

import structlog

from app.workflow_engine.workflow import Workflow, WorkflowRunResult

logger = structlog.get_logger(__name__)


class WorkflowEngine:
    async def run(
        self,
        workflow: Workflow,
        *,
        initial_state: dict[str, Any] | None = None,
    ) -> WorkflowRunResult:
        state: dict[str, Any] = dict(initial_state or {})
        result = WorkflowRunResult(workflow_name=workflow.name, output=state)

        logger.info("workflow_started", workflow=workflow.name)

        for step in workflow.steps:
            try:
                step_output = await step.action(state)
            except Exception as exc:  # noqa: BLE001 — deliberately broad: a
                # workflow step failing must never propagate past the
                # engine; failure is reported in the result, not raised.
                logger.error(
                    "workflow_step_failed",
                    workflow=workflow.name,
                    step=step.name,
                    error=str(exc),
                )
                result.success = False
                result.failed_step = step.name
                result.error = f"Step '{step.name}' failed: {exc}"
                return result

            state.update(step_output)
            result.completed_steps.append(step.name)

        result.output = state
        logger.info("workflow_completed", workflow=workflow.name, steps=result.completed_steps)
        return result
