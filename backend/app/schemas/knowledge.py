"""
Knowledge Agent API schemas.

KnowledgeCitationRead was added first (Slice 6, item 7) — needed so
CompassAskResponse could carry citations back to the frontend before
this endpoint file existed. Document CRUD schemas below complete the
set for app/api/v1/knowledge.py.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class KnowledgeCitationRead(BaseModel):
    document_id: uuid.UUID
    document_title: str
    chunk_id: uuid.UUID
    excerpt: str


class KnowledgeDocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    category: str
    original_filename: str
    content_type: str
    file_size_bytes: int
    status: str
    error_message: str | None
    embedding_model: str | None
    embedding_dimension: int | None
    embedding_version: str | None
    last_processed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class KnowledgeDocumentListResponse(BaseModel):
    items: list[KnowledgeDocumentRead]
    total: int
    page: int
    page_size: int
