"""
WorkspaceContext.

Per the Product Book's AI System Design, "Context Builder" is the most
underestimated step in the pipeline — agents that each re-fetch their own
context independently drift out of sync and duplicate queries. This
object is the single shape every capability (agent or workflow) receives,
built once per Compass invocation.

Slice 0 defines the shape only. The actual ContextBuilder that populates
this from the database (candidate history, job details, notes, prior AI
analyses, etc.) is implemented once those entities exist, starting
Slice 3 (Candidate Application Flow) and extended through Slice 4.
"""

from dataclasses import dataclass, field
from typing import Any

from app.core.roles import Role


@dataclass
class WorkspaceContext:
    #: None for candidates — platform-wide identities, not company
    #: members (see Slice 1's AccountType decision). Every internal role
    #: always has a company_id.
    company_id: str | None
    user_id: str
    role: Role

    #: e.g. "candidate", "job", "employee", "knowledge" — mirrors the
    #: Product Book's Workspace concept (Candidate Workspace, Job Workspace...)
    workspace_type: str | None = None
    workspace_id: str | None = None

    #: Free-form bag for workspace-specific data (resume text, job
    #: description, recent notes...). Typed sub-objects can replace this
    #: per-workspace-type once real workspaces exist; kept generic in
    #: Slice 0 since no workspace data exists yet.
    data: dict[str, Any] = field(default_factory=dict)

    #: Short rolling conversation history for this Compass session.
    conversation: list[dict[str, str]] = field(default_factory=list)
