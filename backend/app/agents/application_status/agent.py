"""
ApplicationStatusAgent.

Not an AI agent — zero LLM calls, deliberately. It exists so
Compass's candidate-facing `application_status` capability goes through
the SAME uniform mechanism as `explain_analysis` (Agent Registry ->
`agent.run(context)`), keeping Compass a pure router that never branches
on "is this an AI capability or not." Slice 0's `Agent`/`AgentResult`
interface never required LLM usage — this is the first concrete proof
that a capability can be a plain deterministic lookup and still fit the
same registry/routing shape as a real AI agent.

Receives already-fetched plain data via `context.payload` (populated by
`compass/context_builder.py`) — it does not call ApplicationService or
touch the database itself, same "receives structured context, doesn't
query arbitrary tables" rule as ResumeIntelligenceAgent.
"""

from app.agents.base import Agent, AgentContext, AgentResult

_STATUS_LABELS = {
    "applied": "Applied",
    "screening": "Screening",
    "interview": "Interview",
    "offer": "Offer",
    "hired": "Hired",
    "rejected": "Rejected",
}


class ApplicationStatusAgent(Agent):
    name = "application_status"

    async def run(self, context: AgentContext) -> AgentResult:
        job_title = context.payload["job_title"]
        status = context.payload["status"]
        label = _STATUS_LABELS.get(status, status)

        message = f"Your application for {job_title} is currently at the '{label}' stage."

        return AgentResult(
            output={"message": message},
            reasoning="Deterministic status lookup — no AI reasoning involved.",
            confidence=1.0,
        )
