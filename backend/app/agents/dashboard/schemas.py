"""
Structured output schema for the Daily Alignment Brief.

The LLM only ever synthesizes prose and suggests next actions on top of
facts DashboardService has already computed deterministically (counts,
which applications are waiting, which jobs are understaffed) — it never
computes a score, a count, or a threshold itself, same "LLM never
touches the numbers" discipline as Resume Intelligence's scoring.
"""

from pydantic import BaseModel, Field


class RecommendedAction(BaseModel):
    label: str = Field(min_length=1, max_length=255)
    #: A plain string, not a UUID type — the LLM may occasionally
    #: recommend something not tied to one specific application (e.g.
    #: "consider promoting the Backend Engineer posting"). Optional and
    #: unvalidated by design; the frontend only uses it as a link if
    #: present and well-formed.
    application_id: str | None = None


class DashboardBriefSchema(BaseModel):
    summary: str = Field(min_length=1, max_length=2000)
    recommended_actions: list[RecommendedAction] = Field(default_factory=list, max_length=5)
