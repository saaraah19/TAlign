"""
Structured output schema for the Communication Agent.

One schema, two prompt builders (rejection / interview invitation) —
the LLM call always returns exactly this shape, never free text. The
agent's job ends at producing a draft; a human always reviews before
anything is marked sent (see app/models/email.py's DRAFT/SENT lifecycle
and app/agents/communication/agent.py's module docstring).
"""

from pydantic import BaseModel, Field


class DraftEmailSchema(BaseModel):
    subject: str = Field(min_length=1, max_length=255)
    body: str = Field(min_length=1)
