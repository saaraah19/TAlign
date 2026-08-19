"""
KnowledgeDocumentService.

Owns the KnowledgeDocument pipeline lifecycle:

    UPLOADED -> TEXT_EXTRACTED -> CHUNKED -> EMBEDDED -> READY
    FAILED reachable from any non-terminal state.

Same two-layer discipline as Job/Application: the DB CHECK constrains
valid *values* only (see the Slice 6 migration); the transition GRAPH
lives here, in `_ALLOWED_TRANSITIONS`, and is validated on every
transition — even though, unlike Job's recruiter-driven PATCH endpoint,
every transition here is service-driven rather than a user-facing
"set arbitrary status" action. The private dict still buys the same
thing Job's does: an accidental out-of-order transition inside this
file's own code becomes a raised exception at the moment it happens,
not a silently-wrong row.

Split matches the approved architecture (Amendment 2) exactly:
  - `upload_document`: UPLOADED -> TEXT_EXTRACTED -> CHUNKED, entirely
    synchronous. Zero network calls — file I/O, pypdf/docx via
    document_text_extraction.py, chunking via knowledge_chunking.py.
    Chunks are persisted with `embedding=NULL` at this stage.
  - `process_embeddings`: CHUNKED -> EMBEDDED -> READY, the ONE step
    with a network call (EmbeddingProvider). Target of a FastAPI
    BackgroundTasks call — see `run_embedding_task` at the bottom,
    mirroring resume_analysis_service.py's `run_resume_analysis_task`
    (opens its own DB session, since a background task runs after the
    triggering request's session has already closed).
  - `reindex`: the Amendment 5 admin action. Deletes existing chunks,
    resets the document to UPLOADED, and re-enters the same pipeline
    `upload_document` uses by reading the already-stored file back off
    disk — it skips re-saving the file, since it's already there.

Failure handling: whole-document retry on embedding failure, not
per-chunk — deliberately not over-engineering partial-chunk state for
an MVP (matches the original proposal's reasoning, see HANDOVER.md item
5). Every failure, at either stage, is caught here and persisted as
`status=FAILED` with `error_message` set — never left as an unhandled
exception bubbling out of a background task, same discipline as
ResumeAnalysisService.

RBAC note: role checks (Admin-only for upload/delete/reindex, per the
approved architecture) live at the API layer via `require_roles`, same
pattern as every other service in this codebase (JobService,
CommunicationService). This service only does the lighter defensive
"acting_user actually belongs to a company" check —
`_assert_internal_with_company`, mirroring JobService's method of the
same name — a service should never trust that its caller enforced its
own preconditions correctly, even though the API layer already does.

Domain events are deliberately NOT emitted for this pipeline in this
slice — Job/Application's domain events exist because a future Workflow
Engine listener will react to business transitions (job published,
candidate hired); nothing in the approved Slice 6 scope calls for a
Workflow Engine reaction to a document finishing indexing. Adding
events later, if a real use case appears, is a small addition, not a
redesign.
"""

import uuid
from datetime import UTC, datetime

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import (
    AuthorizationError,
    DocumentProcessingError,
    FileTooLargeError,
    NotFoundError,
    UnsupportedFileTypeError,
)
from app.core.llm_provider import EmbeddingProvider, get_embedding_provider
from app.models.knowledge_chunk import KnowledgeChunk
from app.models.knowledge_document import DocumentStatus, KnowledgeDocument
from app.models.user import User
from app.repositories.knowledge_chunk_repository import KnowledgeChunkRepository
from app.repositories.knowledge_document_repository import KnowledgeDocumentRepository
from app.utils.document_text_extraction import extract_text
from app.utils.knowledge_chunking import CHUNKING_STRATEGY_VERSION, chunk_text
from app.utils.local_file_storage import (
    read_knowledge_document_file,
    save_knowledge_document_file,
)

logger = structlog.get_logger(__name__)


_ALLOWED_TRANSITIONS: dict[DocumentStatus, set[DocumentStatus]] = {
    DocumentStatus.UPLOADED: {DocumentStatus.TEXT_EXTRACTED, DocumentStatus.FAILED},
    DocumentStatus.TEXT_EXTRACTED: {DocumentStatus.CHUNKED, DocumentStatus.FAILED},
    DocumentStatus.CHUNKED: {DocumentStatus.EMBEDDED, DocumentStatus.FAILED},
    DocumentStatus.EMBEDDED: {DocumentStatus.READY, DocumentStatus.FAILED},
    DocumentStatus.READY: set(),
    DocumentStatus.FAILED: set(),
}


class KnowledgeDocumentService:
    def __init__(
        self,
        db: AsyncSession,
        document_repository: KnowledgeDocumentRepository | None = None,
        chunk_repository: KnowledgeChunkRepository | None = None,
        embedding_provider: EmbeddingProvider | None = None,
    ) -> None:
        self._db = db
        self._documents = document_repository or KnowledgeDocumentRepository(db)
        self._chunks = chunk_repository or KnowledgeChunkRepository(db)
        self._embeddings = embedding_provider or get_embedding_provider()

    # --- Upload (deterministic, synchronous half of the pipeline) ---

    async def upload_document(
        self,
        *,
        acting_user: User,
        title: str,
        category: str,
        filename: str,
        content_type: str,
        content: bytes,
    ) -> KnowledgeDocument:
        self._assert_internal_with_company(acting_user)
        self._assert_valid_file(content_type=content_type, size=len(content))
        assert acting_user.company_id is not None  # guaranteed by the assertion above

        file_path = save_knowledge_document_file(
            company_id=acting_user.company_id, filename=filename, content=content
        )

        document = KnowledgeDocument(
            company_id=acting_user.company_id,
            uploaded_by=acting_user.id,
            title=title,
            category=category,
            file_path=file_path,
            original_filename=filename,
            content_type=content_type,
            file_size_bytes=len(content),
            status=DocumentStatus.UPLOADED.value,
        )
        document = await self._documents.create(document)

        await self._extract_and_chunk(document, content_type=content_type, content=content)

        await self._db.commit()
        return document

    async def reindex(self, *, document_id: uuid.UUID, acting_user: User) -> KnowledgeDocument:
        """
        Amendment 5 — a distinct admin RESET action, not a
        `READY -> UPLOADED` edge in `_ALLOWED_TRANSITIONS` (see module
        docstring: that would read as "going backward", which this
        codebase's state machines already disallow for normal flow).
        Deletes the document's existing chunks, clears its embedding
        provenance, resets status to UPLOADED, and re-enters the same
        synchronous pipeline `upload_document` uses — reading the file
        back off disk rather than re-uploading, since it's already there.
        """
        self._assert_internal_with_company(acting_user)
        assert acting_user.company_id is not None  # guaranteed by the assertion above
        document = await self._documents.get_by_id_for_company(
            document_id, acting_user.company_id
        )
        if document is None:
            raise NotFoundError("Knowledge document not found.")

        await self._chunks.delete_for_document(document.id)

        document.status = DocumentStatus.UPLOADED.value
        document.error_message = None
        document.embedding_model = None
        document.embedding_dimension = None
        document.embedding_version = None
        document.last_processed_at = None

        content = read_knowledge_document_file(document.file_path)
        await self._extract_and_chunk(
            document, content_type=document.content_type, content=content
        )

        await self._db.commit()
        return document

    async def _extract_and_chunk(
        self, document: KnowledgeDocument, *, content_type: str, content: bytes
    ) -> None:
        """
        Shared by `upload_document` and `reindex` — both walk
        UPLOADED -> TEXT_EXTRACTED -> CHUNKED identically, the only
        difference being where the bytes came from. Mutates `document`
        in place and does NOT commit — the caller commits once, after
        this returns, so upload/reindex each stay a single transaction.
        """
        try:
            text = extract_text(content_type=content_type, content=content)
        except Exception as exc:  # noqa: BLE001 — any extraction failure becomes FAILED, never unhandled
            self._fail(document, error=str(exc))
            return
        self._transition(document, DocumentStatus.TEXT_EXTRACTED)

        text_chunks = chunk_text(text)
        if not text_chunks:
            self._fail(document, error="Document produced zero chunks after text extraction.")
            return

        chunk_rows = [
            KnowledgeChunk(
                document_id=document.id,
                company_id=document.company_id,
                chunk_index=tc.index,
                content=tc.content,
                token_count=tc.token_count,
            )
            for tc in text_chunks
        ]
        await self._chunks.create_many(chunk_rows)
        self._transition(document, DocumentStatus.CHUNKED)

    # --- Embedding (the one network-calling step; background task) ---

    async def process_embeddings(self, document_id: uuid.UUID) -> None:
        """
        CHUNKED -> EMBEDDED -> READY. Whole-document retry on failure,
        not per-chunk (see module docstring): a failure partway through
        embedding leaves the document FAILED with none of its chunks
        updated, so re-running this method (or reindex) after fixing
        whatever caused the failure always starts the embedding step
        over from the full chunk set — never resumes from a partial
        position.
        """
        document = await self._documents.get_by_id(document_id)
        if document is None:
            logger.error("knowledge_embedding_document_not_found", document_id=str(document_id))
            return
        if document.status != DocumentStatus.CHUNKED.value:
            logger.warning(
                "knowledge_embedding_wrong_status",
                document_id=str(document_id),
                status=document.status,
            )
            return

        chunks = await self._chunks.list_for_document(document.id)
        if not chunks:
            self._fail(document, error="No chunks found for embedding.")
            await self._db.commit()
            return

        try:
            vectors = await self._embeddings.embed_documents([c.content for c in chunks])
        except Exception as exc:  # noqa: BLE001 — any embedding-call failure becomes FAILED, never unhandled
            self._fail(document, error=str(exc))
            await self._db.commit()
            return

        if len(vectors) != len(chunks):
            self._fail(
                document,
                error=(
                    f"Embedding provider returned {len(vectors)} vectors for "
                    f"{len(chunks)} chunks — refusing to apply a mismatched result."
                ),
            )
            await self._db.commit()
            return

        for chunk, vector in zip(chunks, vectors, strict=True):
            chunk.embedding = vector

        self._transition(document, DocumentStatus.EMBEDDED)
        document.embedding_model = self._embeddings.model_name
        document.embedding_dimension = self._embeddings.dimension
        document.embedding_version = CHUNKING_STRATEGY_VERSION

        self._transition(document, DocumentStatus.READY)
        # App-computed, not a DB server-side timestamp — same precedent as
        # ResumeAnalysis.analyzed_at (resume_analysis_service.py).
        document.last_processed_at = datetime.now(UTC)
        await self._db.commit()

    # --- Reads (recruiter/admin-facing, company-scoped) ---

    async def get_by_id_for_company(
        self, *, document_id: uuid.UUID, acting_user: User
    ) -> KnowledgeDocument:
        self._assert_internal_with_company(acting_user)
        assert acting_user.company_id is not None
        document = await self._documents.get_by_id_for_company(
            document_id, acting_user.company_id
        )
        if document is None:
            raise NotFoundError("Knowledge document not found.")
        return document

    async def list_for_company(
        self,
        *,
        acting_user: User,
        category: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[KnowledgeDocument], int]:
        self._assert_internal_with_company(acting_user)
        assert acting_user.company_id is not None
        return await self._documents.list_for_company(
            acting_user.company_id, category=category, page=page, page_size=page_size
        )

    async def delete_document(self, *, document_id: uuid.UUID, acting_user: User) -> None:
        document = await self.get_by_id_for_company(
            document_id=document_id, acting_user=acting_user
        )
        # Chunks cascade-delete at the DB level — see
        # KnowledgeDocumentRepository.delete's docstring.
        await self._documents.delete(document)

    # --- Internal helpers ---

    def _transition(self, document: KnowledgeDocument, target: DocumentStatus) -> None:
        current = DocumentStatus(document.status)
        allowed = _ALLOWED_TRANSITIONS.get(current, set())
        if target not in allowed:
            raise DocumentProcessingError(
                f"Cannot transition a knowledge document from '{current.value}' to "
                f"'{target.value}'."
            )
        document.status = target.value

    def _fail(self, document: KnowledgeDocument, *, error: str) -> None:
        self._transition(document, DocumentStatus.FAILED)
        document.error_message = error
        logger.warning(
            "knowledge_document_processing_failed", document_id=str(document.id), error=error
        )

    @staticmethod
    def _assert_internal_with_company(user: User) -> None:
        # Defensive check: RBAC at the API layer already restricts these
        # actions to Admin, but a service should never trust that a
        # caller enforced its own preconditions correctly.
        if user.company_id is None:
            raise AuthorizationError("This action requires an internal company account.")

    @staticmethod
    def _assert_valid_file(*, content_type: str, size: int) -> None:
        if content_type not in settings.allowed_document_content_types:
            raise UnsupportedFileTypeError(
                f"Unsupported file type '{content_type}'. Allowed types: "
                f"{', '.join(settings.allowed_document_content_types)}."
            )
        if size > settings.max_knowledge_file_size_bytes:
            max_mb = settings.max_knowledge_file_size_bytes / (1024 * 1024)
            raise FileTooLargeError(f"File exceeds the maximum allowed size of {max_mb:.1f} MB.")


async def run_embedding_task(document_id: uuid.UUID) -> None:
    """
    FastAPI BackgroundTasks entrypoint. Opens its OWN database session —
    mirrors resume_analysis_service.py's run_resume_analysis_task exactly,
    for the same reason: a background task runs after the triggering
    request's session has already closed, so it cannot reuse
    `Depends(get_db)`'s session.
    """
    from app.database.session import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        service = KnowledgeDocumentService(db)
        try:
            await service.process_embeddings(document_id)
        except Exception:  # noqa: BLE001 — background tasks must never raise past this point
            logger.exception(
                "knowledge_embedding_background_task_failed", document_id=str(document_id)
            )
