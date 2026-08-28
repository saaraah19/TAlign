"""
DashboardAgent.

Not registered in the Agent Registry / Compass Capability Registry —
same reasoning as CommunicationAgent and KnowledgeAgent: this is a
plain internal collaborator owned by DashboardService, not something
reachable through Compass's chat-style "ask a question" routing. See
the Slice 8 architecture decision: the Daily Brief is generated on
Dashboard page load (a passive trigger), not a Compass chat turn —
Compass's intent-routing heuristic currently has no way to disambiguate
"give me my brief" from "answer my policy question" for an internal
role with no workspace, and extending it to real intent classification
for one capability wasn't judged worth the risk to Compass's
deliberately-simple pure-router design. If a future slice adds "ask
Compass for today's brief" as a conversational capability, that's a
Compass-layer routing addition, not a change to this Agent's own
boundary.

This agent's responsibility ends at producing prose + a short
suggested-actions list from data it's handed. It never queries the
database (DashboardService does all the aggregation and hands this
agent only plain dicts/strings -- see build_daily_brief_prompt), and it
never decides what counts as "low applicant volume" or "awaiting
review" (those thresholds and filters are DashboardService's
deterministic logic, computed before this agent is ever called).
"""

from dataclasses import dataclass

from app.agents.dashboard.prompts import DAILY_BRIEF_PROMPT_VERSION, build_daily_brief_prompt
from app.agents.dashboard.schemas import DashboardBriefSchema
from app.agents.shared.structured_output import complete_structured_with_one_retry
from app.core.llm_provider import LLMProvider, get_llm_provider


@dataclass(frozen=True)
class BriefOutcome:
    schema: DashboardBriefSchema
    llm_provider: str
    llm_model: str
    prompt_version: str


class DashboardAgent:
    def __init__(self, llm_provider: LLMProvider | None = None) -> None:
        self._llm = llm_provider or get_llm_provider()

    async def generate_daily_brief(
        self,
        *,
        recruiter_first_name: str,
        company_name: str,
        pending_drafts_count: int,
        awaiting_review: list[dict[str, str]],
        low_applicant_jobs: list[dict[str, str]],
        recent_analyses: list[dict[str, str]],
    ) -> BriefOutcome:
        messages = build_daily_brief_prompt(
            recruiter_first_name=recruiter_first_name,
            company_name=company_name,
            pending_drafts_count=pending_drafts_count,
            awaiting_review=awaiting_review,
            low_applicant_jobs=low_applicant_jobs,
            recent_analyses=recent_analyses,
        )
        schema = await complete_structured_with_one_retry(
            self._llm, messages, DashboardBriefSchema
        )
        return BriefOutcome(
            schema=schema,
            llm_provider=self._provider_name(),
            llm_model=self._model_name(),
            prompt_version=DAILY_BRIEF_PROMPT_VERSION,
        )

    def _provider_name(self) -> str:
        return type(self._llm).__name__.replace("Provider", "").lower()

    def _model_name(self) -> str:
        return getattr(self._llm, "_default_model", "unknown")
