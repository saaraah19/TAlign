"""
WorkflowContext types.

A Workflow's internal steps should never pass raw SQLAlchemy model
instances to each other or to the Agents/Services they call — that
couples every consumer to the ORM shape and makes it easy to
accidentally leak internal-only fields the way an Application or
Employee row might carry. Instead, `HireCandidateWorkflow` fetches
everything it needs ONCE at the start of a run, extracts it into this
plain, frozen dataclass, and every step thereafter — including the
call into `CommunicationService` for the welcome-email draft — passes
around only this structured, primitive-typed data.

This mirrors the discipline `app/agents/communication/agent.py` already
enforces at its own boundary (plain strings only, never a DB session or
model) — `HireWorkflowContext` extends that same discipline one layer
further out, to the workflow's internal step-to-step data flow.
"""

import uuid
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, kw_only=True)
class HireWorkflowContext:
    application_id: uuid.UUID
    company_id: uuid.UUID
    company_name: str
    candidate_first_name: str
    candidate_last_name: str
    candidate_email: str
    job_title: str
    hire_date: date
