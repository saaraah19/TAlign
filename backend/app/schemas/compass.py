"""Compass schemas."""

import uuid

from pydantic import BaseModel

from app.schemas.knowledge import KnowledgeCitationRead


class CompassAskRequest(BaseModel):
    message: str
    #: Optional — required for workspace-scoped capabilities
    #: (explain_analysis, application_status), absent for
    #: workspace-independent ones (knowledge_query). See
    #: Compass._resolve_capability_for_role's docstring for how the
    #: presence/absence of this field drives routing for internal roles.
    application_id: uuid.UUID | None = None


class CompassAskResponse(BaseModel):
    message: str
    capability_used: str | None
    #: Populated only when capability_used == "knowledge_query" and an
    #: answer was actually grounded in retrieved documents.
    citations: list[KnowledgeCitationRead] | None = None
    #: RetrievalConfidence value ("high"/"medium"/"low"), or None for
    #: every other capability and for Knowledge's own deterministic
    #: "no relevant documents found" case (see confidence.py).
    confidence: str | None = None
