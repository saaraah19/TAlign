"""
Prompt construction for the Daily Alignment Brief.

Content-safety-style discipline, same shape as
app/agents/communication/prompts.py, applied here for a different
reason: not to prevent candidate-facing leakage (this brief is
recruiter-only, never shown to a candidate), but to keep the LLM's job
narrowly "write prose and suggest priorities from already-computed
facts" rather than "decide what matters." The prompt builder's
signature only accepts plain counts and short lists of already-
aggregated summaries (candidate name, job title, a score, a day count)
— never a raw ResumeAnalysis row, an Application ORM object, or
anything the LLM could use to invent a number that isn't already true.

Every recommended action must reference something that already exists
in the data handed to the prompt — the system prompt says so
explicitly, and DashboardService validates any `application_id` a
recommendation names against the set of applications actually passed
in (see DashboardService._validate_recommended_actions), same
citation-validation discipline as the Knowledge Agent's anti-
hallucination gate.
"""

from app.core.llm_provider import LLMMessage

DAILY_BRIEF_PROMPT_VERSION = "daily_brief_v1"

_SYSTEM_PROMPT = """
You are Compass, an AI assistant embedded in an HR/recruiting platform, writing
a short "Daily Alignment Brief" for a recruiter opening their dashboard.

Rules:
- Write 2-4 sentences of natural, warm, professional prose — like a
  colleague giving a quick morning summary, not a robotic report.
- Base everything ONLY on the facts provided below. Never invent a number,
  a name, or a status that isn't given to you.
- Then suggest at most 5 concrete next actions, each a short label (e.g.
  "Review Ahmed's application", "Follow up on the Backend Engineer posting").
  Every action must be about something that appears in the facts below — do
  not suggest anything unrelated to the provided data.
- If application_id is available for the specific application an action
  refers to, include it; otherwise leave it null.
- If there is genuinely little to report (few or no pending items), say so
  briefly and warmly rather than padding with generic advice.
""".strip()


def build_daily_brief_prompt(
    *,
    recruiter_first_name: str,
    company_name: str,
    pending_drafts_count: int,
    awaiting_review: list[dict[str, str]],
    low_applicant_jobs: list[dict[str, str]],
    recent_analyses: list[dict[str, str]],
) -> list[LLMMessage]:
    """
    Each list item is a plain dict of already-stringified fields (never
    a raw model) — e.g. awaiting_review entries look like
    {"application_id": "...", "candidate_name": "...", "job_title": "...",
    "days_waiting": "3"}.
    """
    facts_lines = [
        f"Recruiter: {recruiter_first_name}",
        f"Company: {company_name}",
        f"Draft emails awaiting review/send: {pending_drafts_count}",
        "",
        "Applications awaiting review:",
    ]
    if awaiting_review:
        for item in awaiting_review:
            facts_lines.append(
                f"- {item.get('candidate_name')} for {item.get('job_title')} "
                f"(application_id: {item.get('application_id')}, "
                f"waiting {item.get('days_waiting')} days)"
            )
    else:
        facts_lines.append("- none")

    facts_lines.append("")
    facts_lines.append("Open jobs with low applicant volume:")
    if low_applicant_jobs:
        for item in low_applicant_jobs:
            facts_lines.append(
                f"- {item.get('job_title')}: {item.get('applicant_count')} applicants"
            )
    else:
        facts_lines.append("- none")

    facts_lines.append("")
    facts_lines.append("Recently completed resume analyses:")
    if recent_analyses:
        for item in recent_analyses:
            facts_lines.append(
                f"- {item.get('candidate_name')} for {item.get('job_title')}: "
                f"score {item.get('score')} "
                f"(application_id: {item.get('application_id')})"
            )
    else:
        facts_lines.append("- none")

    system = LLMMessage(role="system", content=_SYSTEM_PROMPT)
    user = LLMMessage(role="user", content="\n".join(facts_lines))
    return [system, user]
