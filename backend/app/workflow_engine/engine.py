"""
Workflow Engine runner.

Owns sequencing, not business rules. This class is intentionally "dumb":
it walks `workflow.steps` in order, resolves the agent for any step that
requires one via the Agent Registry, and calls `workflow.execute_step`.
It has no knowledge of hiring, onboarding, or any specific business
process — that knowledge lives entirely inside each Workflow subclass.
"""

from typing import Any

import structlog

from app.agents.base import AgentContext
from app.agents.registry import AgentRegistry, agent_registry
from app.workflow_engine.workflow import Workflow, WorkflowRunResult

logger = structlog.get_logger(__name__)


class WorkflowEngine:
    def __init__(self, registry: AgentRegistry = agent_registry) -> None:
        self._agent_registry = registry

    async def run(
        self,
        workflow: Workflow,
        *,
        company_id: str,
        user_id: str,
        initial_state: dict[str, Any] | None = None,
    ) -> WorkflowRunResult:
        state: dict[str, Any] = dict(initial_state or {})
        result = WorkflowRunResult(workflow_name=workflow.name, output=state)

        logger.info("workflow_started", workflow=workflow.name, user_id=user_id)

        for step in workflow.steps:
            agent_output: dict[str, Any] | None = None

            if step.requires_agent:
                assert step.agent_capability is not None  # enforced in WorkflowStep
                agent = self._agent_registry.get(step.agent_capability)
                agent_result = await agent.run(
                    AgentContext(company_id=company_id, user_id=user_id, payload=state)
                )
                agent_output = agent_result.output
                logger.info(
                    "workflow_step_agent_invoked",
                    workflow=workflow.name,
                    step=step.name,
                    capability=step.agent_capability,
                )

            try:
                step_output = await workflow.execute_step(step, state, agent_output)
            except Exception as exc:  # noqa: BLE001 — deliberately broad: workflow steps
                # must never take down the request; failure is reported in the result.
                logger.error(
                    "workflow_step_failed", workflow=workflow.name, step=step.name, error=str(exc)
                )
                result.success = False
                result.error = f"Step '{step.name}' failed: {exc}"
                return result

            state.update(step_output)
            result.completed_steps.append(step.name)

        result.output = state
        logger.info("workflow_completed", workflow=workflow.name, steps=result.completed_steps)
        return result
