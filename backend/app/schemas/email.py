"""Email schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.email import EmailType


class DraftEmailRequest(BaseModel):
    email_type: EmailType


class UpdateEmailRequest(BaseModel):
    subject: str = Field(min_length=1, max_length=255)
    body: str = Field(min_length=1)


class EmailRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    application_id: uuid.UUID
    email_type: str
    status: str
    recipient_email: str
    subject: str
    body: str
    llm_provider: str | None
    llm_model: str | None
    prompt_version: str | None
    sent_at: datetime | None
    created_at: datetime
    updated_at: datetime


class EmailListResponse(BaseModel):
    items: list[EmailRead]
