"""
Dedicated cross-tenant isolation test for the Knowledge Agent's vector
retrieval query — per HANDOVER.md's explicit instruction: "given the
severity of a cross-tenant leak here, this needs its own dedicated
test, not just inherited confidence from the pattern used elsewhere."

Two layers of proof, deliberately not just one:

  1. `test_search_similar_query_filters_by_company_id` inspects the
     ACTUAL SQLAlchemy statement `search_similar` builds at runtime
     (captured via a mocked AsyncSession's `execute` call) and asserts
     the compiled SQL contains a `company_id = ...` predicate. This
     catches a regression where someone edits the query and drops the
     filter, even if every other test still passes with mocked data
     (mocked repositories elsewhere in this codebase can't catch that
     class of bug — they only prove the method was called, not that the
     query it built was correct).

  2. `test_search_similar_passes_distinct_company_ids_through_unchanged`
     proves the filter value passed to the query is exactly the
     `company_id` argument given to the method — not a hardcoded
     constant, not silently substituted, for two different companies.

No live Postgres is available in this sandbox (see HANDOVER.md), so
these tests verify the statement's shape/parameters rather than
executing it against real data — the same constraint every other test
in this suite already works within.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock

from sqlalchemy.dialects import postgresql

from app.repositories.knowledge_chunk_repository import KnowledgeChunkRepository


def _make_repo_with_captured_statement() -> tuple[KnowledgeChunkRepository, AsyncMock]:
    db = AsyncMock()
    result = MagicMock()  # Result.all() is synchronous, even though db.execute() is async
    result.all.return_value = []
    db.execute.return_value = result
    return KnowledgeChunkRepository(db), db


def _compile(statement: object) -> str:
    # The generic SQL compiler can't literal-render postgresql's UUID
    # column type (KnowledgeChunk.company_id) — must compile against the
    # postgresql dialect explicitly, same dialect this project targets
    # in production (see alembic env.py / docker-compose.yml).
    return str(statement.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}))


async def test_search_similar_query_filters_by_company_id() -> None:
    repo, db = _make_repo_with_captured_statement()
    company_id = uuid.uuid4()

    await repo.search_similar(
        company_id=company_id, query_embedding=[0.1] * 768, top_k=5
    )

    executed_statement = db.execute.await_args.args[0]
    compiled = _compile(executed_statement)

    assert f"knowledge_chunks.company_id = '{company_id}'" in compiled
    assert "knowledge_chunks.embedding IS NOT NULL" in compiled
    # Confirms the cosine-distance operator drives ordering (pgvector's `<=>`).
    assert "<=>" in compiled


async def test_search_similar_passes_distinct_company_ids_through_unchanged() -> None:
    repo, db = _make_repo_with_captured_statement()

    company_a = uuid.uuid4()
    company_b = uuid.uuid4()

    await repo.search_similar(company_id=company_a, query_embedding=[0.1] * 768, top_k=5)
    statement_a = db.execute.await_args.args[0]
    compiled_a = _compile(statement_a)

    await repo.search_similar(company_id=company_b, query_embedding=[0.1] * 768, top_k=5)
    statement_b = db.execute.await_args.args[0]
    compiled_b = _compile(statement_b)

    assert str(company_a) in compiled_a
    assert str(company_a) not in compiled_b
    assert str(company_b) in compiled_b
    assert str(company_b) not in compiled_a
