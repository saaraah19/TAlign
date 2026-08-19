"""
Tests for KnowledgeDocumentService's pipeline: upload (sync
extract+chunk), embedding (background step), and reindex.

Same pattern as test_application_service_rules.py: mocked repositories
and a mocked AsyncSession, no live database. The embedding step uses
FakeEmbeddingProvider (tests/fakes.py) rather than a plain mock, so
assertions can check real vector shapes/counts instead of just call
counts.
"""

import uuid
from unittest.mock import AsyncMock, patch

import pytest

from app.core.exceptions import (
    AuthorizationError,
    DocumentProcessingError,
    FileTooLargeError,
    NotFoundError,
    UnsupportedFileTypeError,
)
from app.core.roles import AccountType
from app.models.knowledge_chunk import KnowledgeChunk
from app.models.knowledge_document import DocumentCategory, DocumentStatus, KnowledgeDocument
from app.models.user import User
from app.services.knowledge_document_service import KnowledgeDocumentService
from tests.fakes import FakeEmbeddingProvider

_VALID_TEXT = ("This is a policy document with real sentences. " * 20).strip()


def _make_admin(company_id: uuid.UUID | None = None) -> User:
    return User(
        id=uuid.uuid4(),
        company_id=company_id or uuid.uuid4(),
        account_type=AccountType.INTERNAL.value,
        email="admin@example.com",
        password_hash="x",
        first_name="Olivia",
        last_name="Brown",
    )


def _make_candidate() -> User:
    return User(
        id=uuid.uuid4(),
        company_id=None,
        account_type=AccountType.CANDIDATE.value,
        email="candidate@example.com",
        password_hash="x",
        first_name="Alex",
        last_name="Johnson",
    )


def _make_document(
    *, company_id: uuid.UUID, status: DocumentStatus = DocumentStatus.CHUNKED
) -> KnowledgeDocument:
    return KnowledgeDocument(
        id=uuid.uuid4(),
        company_id=company_id,
        title="Leave Policy",
        category=DocumentCategory.POLICY.value,
        file_path="/tmp/fake.txt",
        original_filename="leave_policy.txt",
        content_type="text/plain",
        file_size_bytes=100,
        status=status.value,
    )


def _make_chunks(document: KnowledgeDocument, count: int) -> list[KnowledgeChunk]:
    return [
        KnowledgeChunk(
            id=uuid.uuid4(),
            document_id=document.id,
            company_id=document.company_id,
            chunk_index=i,
            content=f"chunk {i} content",
            token_count=3,
        )
        for i in range(count)
    ]


def _make_service(
    *,
    document_repo: AsyncMock | None = None,
    chunk_repo: AsyncMock | None = None,
    embedding_provider: FakeEmbeddingProvider | None = None,
) -> KnowledgeDocumentService:
    document_repo = document_repo or AsyncMock()
    document_repo.create.side_effect = lambda doc: doc  # id already set by caller in these tests

    chunk_repo = chunk_repo or AsyncMock()
    chunk_repo.create_many.side_effect = lambda chunks: chunks

    db = AsyncMock()

    return KnowledgeDocumentService(
        db,
        document_repository=document_repo,
        chunk_repository=chunk_repo,
        embedding_provider=embedding_provider or FakeEmbeddingProvider(),
    )


# --- upload_document ---


async def test_upload_document_happy_path_reaches_chunked_status() -> None:
    admin = _make_admin()
    document_repo = AsyncMock()
    document_repo.create.side_effect = lambda doc: doc
    chunk_repo = AsyncMock()
    chunk_repo.create_many.side_effect = lambda chunks: chunks
    service = _make_service(document_repo=document_repo, chunk_repo=chunk_repo)

    with patch(
        "app.services.knowledge_document_service.save_knowledge_document_file",
        return_value="/tmp/fake_path.txt",
    ):
        document = await service.upload_document(
            acting_user=admin,
            title="Leave Policy",
            category=DocumentCategory.POLICY.value,
            filename="leave_policy.txt",
            content_type="text/plain",
            content=_VALID_TEXT.encode("utf-8"),
        )

    assert document.status == DocumentStatus.CHUNKED.value
    assert document.error_message is None
    chunk_repo.create_many.assert_awaited_once()
    persisted_chunks = chunk_repo.create_many.await_args.args[0]
    assert len(persisted_chunks) >= 1
    assert all(c.company_id == admin.company_id for c in persisted_chunks)


async def test_upload_document_rejects_non_internal_user() -> None:
    service = _make_service()
    with pytest.raises(AuthorizationError):
        await service.upload_document(
            acting_user=_make_candidate(),
            title="Leave Policy",
            category=DocumentCategory.POLICY.value,
            filename="x.txt",
            content_type="text/plain",
            content=_VALID_TEXT.encode("utf-8"),
        )


async def test_upload_document_rejects_unsupported_content_type() -> None:
    service = _make_service()
    with pytest.raises(UnsupportedFileTypeError):
        await service.upload_document(
            acting_user=_make_admin(),
            title="Leave Policy",
            category=DocumentCategory.POLICY.value,
            filename="x.exe",
            content_type="application/x-msdownload",
            content=b"whatever",
        )


async def test_upload_document_rejects_oversized_file() -> None:
    service = _make_service()
    oversized = b"a" * (21 * 1024 * 1024)  # over the 20MB knowledge limit
    with pytest.raises(FileTooLargeError):
        await service.upload_document(
            acting_user=_make_admin(),
            title="Leave Policy",
            category=DocumentCategory.POLICY.value,
            filename="big.txt",
            content_type="text/plain",
            content=oversized,
        )


async def test_upload_document_extraction_failure_marks_failed() -> None:
    admin = _make_admin()
    service = _make_service()

    with patch(
        "app.services.knowledge_document_service.save_knowledge_document_file",
        return_value="/tmp/fake_path.pdf",
    ):
        document = await service.upload_document(
            acting_user=admin,
            title="Corrupt PDF",
            category=DocumentCategory.OTHER.value,
            filename="corrupt.pdf",
            content_type="application/pdf",
            content=b"not a real pdf",
        )

    assert document.status == DocumentStatus.FAILED.value
    assert document.error_message is not None


async def test_upload_document_zero_chunks_marks_failed() -> None:
    admin = _make_admin()
    service = _make_service()

    with (
        patch(
            "app.services.knowledge_document_service.save_knowledge_document_file",
            return_value="/tmp/fake_path.txt",
        ),
        patch("app.services.knowledge_document_service.chunk_text", return_value=[]),
    ):
        document = await service.upload_document(
            acting_user=admin,
            title="Empty After Chunking",
            category=DocumentCategory.OTHER.value,
            filename="x.txt",
            content_type="text/plain",
            content=_VALID_TEXT.encode("utf-8"),
        )

    assert document.status == DocumentStatus.FAILED.value
    assert "zero chunks" in (document.error_message or "").lower()


# --- process_embeddings ---


async def test_process_embeddings_happy_path_reaches_ready() -> None:
    admin_company_id = uuid.uuid4()
    document = _make_document(company_id=admin_company_id, status=DocumentStatus.CHUNKED)
    chunks = _make_chunks(document, 3)

    document_repo = AsyncMock()
    document_repo.get_by_id.return_value = document
    chunk_repo = AsyncMock()
    chunk_repo.list_for_document.return_value = chunks

    embedding_provider = FakeEmbeddingProvider(dimension=8)
    service = _make_service(
        document_repo=document_repo, chunk_repo=chunk_repo, embedding_provider=embedding_provider
    )

    await service.process_embeddings(document.id)

    assert document.status == DocumentStatus.READY.value
    assert document.embedding_model == "fake-embedding-model"
    assert document.embedding_dimension == 8
    assert document.embedding_version is not None
    assert document.last_processed_at is not None
    assert all(len(c.embedding) == 8 for c in chunks)


async def test_process_embeddings_wrong_status_is_a_noop() -> None:
    document = _make_document(company_id=uuid.uuid4(), status=DocumentStatus.READY)
    document_repo = AsyncMock()
    document_repo.get_by_id.return_value = document
    chunk_repo = AsyncMock()
    service = _make_service(document_repo=document_repo, chunk_repo=chunk_repo)

    await service.process_embeddings(document.id)

    chunk_repo.list_for_document.assert_not_awaited()
    assert document.status == DocumentStatus.READY.value  # unchanged


async def test_process_embeddings_no_chunks_marks_failed() -> None:
    document = _make_document(company_id=uuid.uuid4(), status=DocumentStatus.CHUNKED)
    document_repo = AsyncMock()
    document_repo.get_by_id.return_value = document
    chunk_repo = AsyncMock()
    chunk_repo.list_for_document.return_value = []
    service = _make_service(document_repo=document_repo, chunk_repo=chunk_repo)

    await service.process_embeddings(document.id)

    assert document.status == DocumentStatus.FAILED.value


async def test_process_embeddings_provider_failure_marks_failed() -> None:
    document = _make_document(company_id=uuid.uuid4(), status=DocumentStatus.CHUNKED)
    chunks = _make_chunks(document, 2)
    document_repo = AsyncMock()
    document_repo.get_by_id.return_value = document
    chunk_repo = AsyncMock()
    chunk_repo.list_for_document.return_value = chunks

    from app.core.exceptions import LLMProviderError

    embedding_provider = FakeEmbeddingProvider(
        document_vectors=LLMProviderError("simulated embedding API failure")
    )
    service = _make_service(
        document_repo=document_repo, chunk_repo=chunk_repo, embedding_provider=embedding_provider
    )

    await service.process_embeddings(document.id)

    assert document.status == DocumentStatus.FAILED.value
    assert "simulated embedding api failure" in (document.error_message or "").lower()


async def test_process_embeddings_vector_count_mismatch_marks_failed() -> None:
    document = _make_document(company_id=uuid.uuid4(), status=DocumentStatus.CHUNKED)
    chunks = _make_chunks(document, 3)
    document_repo = AsyncMock()
    document_repo.get_by_id.return_value = document
    chunk_repo = AsyncMock()
    chunk_repo.list_for_document.return_value = chunks

    embedding_provider = FakeEmbeddingProvider(document_vectors=[[0.1] * 8, [0.2] * 8])  # 2 != 3
    service = _make_service(
        document_repo=document_repo, chunk_repo=chunk_repo, embedding_provider=embedding_provider
    )

    await service.process_embeddings(document.id)

    assert document.status == DocumentStatus.FAILED.value
    assert "mismatch" in (document.error_message or "").lower()


# --- reindex ---


async def test_reindex_deletes_chunks_and_restarts_pipeline() -> None:
    admin = _make_admin()
    document = _make_document(company_id=admin.company_id, status=DocumentStatus.READY)
    document.embedding_model = "old-model"
    document.embedding_dimension = 768
    document.embedding_version = "old-version"

    document_repo = AsyncMock()
    document_repo.get_by_id_for_company.return_value = document
    chunk_repo = AsyncMock()
    chunk_repo.create_many.side_effect = lambda chunks: chunks
    service = _make_service(document_repo=document_repo, chunk_repo=chunk_repo)

    with patch(
        "app.services.knowledge_document_service.read_knowledge_document_file",
        return_value=_VALID_TEXT.encode("utf-8"),
    ):
        result = await service.reindex(document_id=document.id, acting_user=admin)

    chunk_repo.delete_for_document.assert_awaited_once_with(document.id)
    assert result.status == DocumentStatus.CHUNKED.value
    assert result.embedding_model is None
    assert result.embedding_dimension is None
    assert result.embedding_version is None
    assert result.last_processed_at is None


async def test_reindex_missing_document_raises_not_found() -> None:
    admin = _make_admin()
    document_repo = AsyncMock()
    document_repo.get_by_id_for_company.return_value = None
    service = _make_service(document_repo=document_repo)

    with pytest.raises(NotFoundError):
        await service.reindex(document_id=uuid.uuid4(), acting_user=admin)


# --- transition graph guard ---


def test_invalid_transition_raises_processing_error() -> None:
    service = _make_service()
    document = _make_document(company_id=uuid.uuid4(), status=DocumentStatus.READY)

    with pytest.raises(DocumentProcessingError):
        service._transition(document, DocumentStatus.UPLOADED)
