"""Resume schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ResumeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    candidate_id: uuid.UUID
    original_filename: str
    content_type: str
    file_size_bytes: int
    status: str
    parse_error: str | None
    created_at: datetime
