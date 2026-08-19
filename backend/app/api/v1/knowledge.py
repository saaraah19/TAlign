"""
Knowledge Center endpoints — document management only.

Querying goes through the EXISTING /compass/ask endpoint, not a route
here — Knowledge Agent's query-answering IS the Compass interaction
(see app/compass/compass.py's module docstring and
KnowledgeQueryService's). This file only covers uploading, listing,
inspecting, deleting, and reindexing the documents that querying reads
from.

RBAC split, per the approved Slice 6 architecture (HANDOVER.md §3):
  - Management (upload/delete/reindex): ADMIN only — curating official
    company policy content is a governance action, not day-to-day
    recruiter work.
  - Read (list/get): ADMIN, RECRUITER, HIRING_MANAGER — the same three
    roles the knowledge_query Compass capability is scoped to (see
    app/compass/capabilities.py). Not explicitly specified in the
    original proposal the way management access was; this is this
    slice's own default, flagged here for easy revision if it's wrong
    — same "Slice N default, not gospel" pattern jobs.py's RBAC split
    uses for read vs. write access.
"""

import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.core.roles import Role
from app.database.session import get_db
from app.models.knowledge_document import DocumentCategory
from app.models.user import User
from app.schemas.knowledge import KnowledgeDocumentListResponse, KnowledgeDocumentRead
from app.services.knowledge_document_service import KnowledgeDocumentService, run_embedding_task

router = APIRouter()

_READ_ROLES = (Role.ADMIN, Role.RECRUITER, Role.HIRING_MANAGER)
_MANAGE_ROLES = (Role.ADMIN,)


@router.post("/documents", response_model=KnowledgeDocumentRead, status_code=201)
async def upload_knowledge_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: str = Form(...),
    category: DocumentCategory = Form(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*_MANAGE_ROLES)),
) -> KnowledgeDocumentRead:
    """
    Runs the synchronous half of the pipeline (extract + chunk) inline,
    then schedules the embedding step in the background — same split
    as attach_resume_to_application. The response returns as soon as
    chunking finishes; the document's `status` field is how a client
    polls for READY (or FAILED with `error_message` set).
    """
    content = await file.read()
    service = KnowledgeDocumentService(db)
    document = await service.upload_document(
        acting_user=current_user,
        title=title,
        category=category.value,
        filename=file.filename or "document",
        content_type=file.content_type or "application/octet-stream",
        content=content,
    )
    background_tasks.add_task(run_embedding_task, document.id)
    # Re-fetch rather than serializing `document` directly: after
    # upload_document()'s commit(), `updated_at` (a server-side
    # onupdate=func.now() column) is left expired on the in-memory
    # instance. Reading it synchronously inside Pydantic's
    # model_validate raises MissingGreenlet — same bug class already
    # fixed once in jobs.py/applications.py (see their docstrings on
    # this exact pattern), which I missed applying here originally.
    full = await service.get_by_id_for_company(document_id=document.id, acting_user=current_user)
    return KnowledgeDocumentRead.model_validate(full)


@router.get("/documents", response_model=KnowledgeDocumentListResponse)
async def list_knowledge_documents(
    category: DocumentCategory | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*_READ_ROLES)),
) -> KnowledgeDocumentListResponse:
    documents, total = await KnowledgeDocumentService(db).list_for_company(
        acting_user=current_user,
        category=category.value if category else None,
        page=page,
        page_size=page_size,
    )
    return KnowledgeDocumentListResponse(
        items=[KnowledgeDocumentRead.model_validate(d) for d in documents],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/documents/{document_id}", response_model=KnowledgeDocumentRead)
async def get_knowledge_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*_READ_ROLES)),
) -> KnowledgeDocumentRead:
    document = await KnowledgeDocumentService(db).get_by_id_for_company(
        document_id=document_id, acting_user=current_user
    )
    return KnowledgeDocumentRead.model_validate(document)


@router.delete("/documents/{document_id}", status_code=204)
async def delete_knowledge_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*_MANAGE_ROLES)),
) -> None:
    await KnowledgeDocumentService(db).delete_document(
        document_id=document_id, acting_user=current_user
    )


@router.post("/documents/{document_id}/reindex", response_model=KnowledgeDocumentRead)
async def reindex_knowledge_document(
    document_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*_MANAGE_ROLES)),
) -> KnowledgeDocumentRead:
    """Amendment 5 — see KnowledgeDocumentService.reindex's docstring."""
    service = KnowledgeDocumentService(db)
    document = await service.reindex(document_id=document_id, acting_user=current_user)
    background_tasks.add_task(run_embedding_task, document.id)
    # Same re-fetch-before-serializing fix as upload_knowledge_document
    # above — reindex() also ends in a commit().
    full = await service.get_by_id_for_company(document_id=document.id, acting_user=current_user)
    return KnowledgeDocumentRead.model_validate(full)