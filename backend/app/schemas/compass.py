"""Compass schemas."""

import uuid

from pydantic import BaseModel


class CompassAskRequest(BaseModel):
    message: str
    application_id: uuid.UUID


class CompassAskResponse(BaseModel):
    message: str
    capability_used: str | None
