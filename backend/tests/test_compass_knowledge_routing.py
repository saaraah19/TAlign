"""
Tests for Compass.handle_message's routing to the knowledge_query
capability — the service-backed dispatch path added in Slice 6, plus
the workspace_id-based disambiguation between explain_analysis and
knowledge_query for internal roles.

Mocked KnowledgeQueryService (injected via Compass's constructor, same
pattern as every other *Service in this codebase) — no live database,
no real agent registry entries needed since knowledge_query never goes
through agent_registry (see compass.py's module docstring for why).
"""

import uuid
from unittest.mock import AsyncMock

from app.agents.knowledge.confidence import RetrievalConfidence
from app.agents.knowledge.schemas import Citation
from app.compass.capabilities import register_default_capabilities
from app.compass.compass import Compass, CompassResponse
from app.compass.context import WorkspaceContext
from app.core.roles import Role
from app.models.user import User
from app.services.knowledge_query_service import KnowledgeQueryResult


def setup_function() -> None:
    register_default_capabilities()


def _make_recruiter(company_id: uuid.UUID) -> User:
    return User(
        id=uuid.uuid4(),
        company_id=company_id,
        account_type="internal",
        email="emma@example.com",
        password_hash="x",
        first_name="Emma",
        last_name="Martin",
    )


async def test_internal_role_with_no_workspace_routes_to_knowledge_query() -> None:
    company_id = uuid.uuid4()
    recruiter = _make_recruiter(company_id)

    knowledge_service = AsyncMock()
    knowledge_service.ask.return_value = KnowledgeQueryResult(
        answer="You accrue 25 days of annual leave per year.",
        citations=[
            Citation(
                document_id=uuid.uuid4(),
                document_title="Leave Policy",
                chunk_id=uuid.uuid4(),
                excerpt="Employees accrue 25 days of annual leave per year.",
            )
        ],
        grounded=True,
        confidence=RetrievalConfidence.HIGH,
        confidence_algorithm_version="similarity_bands_v1",
    )

    db = AsyncMock()
    compass = Compass(db, knowledge_query_service=knowledge_service)

    context = WorkspaceContext(
        company_id=str(company_id),
        user_id=str(recruiter.id),
        role=Role.RECRUITER,
        workspace_type=None,
        workspace_id=None,  # no application in view -> knowledge_query
        data={"current_user": recruiter},
    )

    response = await compass.handle_message("How many leave days do I get?", context)

    assert response.capability_used == "knowledge_query"
    assert response.message == "You accrue 25 days of annual leave per year."
    assert response.confidence == RetrievalConfidence.HIGH
    assert response.citations is not None
    assert len(response.citations) == 1
    knowledge_service.ask.assert_awaited_once()
    call_kwargs = knowledge_service.ask.await_args.kwargs
    assert call_kwargs["question"] == "How many leave days do I get?"
    assert call_kwargs["acting_user"] is recruiter


async def test_internal_role_with_workspace_does_not_route_to_knowledge_query() -> None:
    """
    A workspace IS in view, so this must resolve to explain_analysis,
    never knowledge_query — regardless of what the message says.
    KnowledgeQueryService must not be touched at all in this case.
    """
    company_id = uuid.uuid4()
    recruiter = _make_recruiter(company_id)

    knowledge_service = AsyncMock()
    db = AsyncMock()
    compass = Compass(db, knowledge_query_service=knowledge_service)

    context = WorkspaceContext(
        company_id=str(company_id),
        user_id=str(recruiter.id),
        role=Role.RECRUITER,
        workspace_type="application",
        workspace_id=str(uuid.uuid4()),
        data={"current_user": recruiter},
    )

    response = await compass.handle_message("Tell me about this policy", context)

    knowledge_service.ask.assert_not_awaited()
    # It will fail to find the (nonexistent, mocked-away) application —
    # the point of this test is only that it never reaches knowledge_query.
    assert response.capability_used != "knowledge_query"


async def test_candidate_role_never_routes_to_knowledge_query() -> None:
    """Candidates have no access to knowledge_query at all, workspace_id or not."""
    knowledge_service = AsyncMock()
    db = AsyncMock()
    compass = Compass(db, knowledge_query_service=knowledge_service)

    candidate = User(
        id=uuid.uuid4(),
        company_id=None,
        account_type="candidate",
        email="alex@example.com",
        password_hash="x",
        first_name="Alex",
        last_name="Johnson",
    )
    context = WorkspaceContext(
        company_id=None,
        user_id=str(candidate.id),
        role=Role.CANDIDATE,
        workspace_type=None,
        workspace_id=None,
        data={"current_user": candidate},
    )

    response = await compass.handle_message("What are my leave days?", context)

    knowledge_service.ask.assert_not_awaited()
    assert response.capability_used != "knowledge_query"
    assert isinstance(response, CompassResponse)


async def test_employee_role_gets_no_capability_at_all() -> None:
    knowledge_service = AsyncMock()
    db = AsyncMock()
    compass = Compass(db, knowledge_query_service=knowledge_service)

    employee = User(
        id=uuid.uuid4(),
        company_id=uuid.uuid4(),
        account_type="internal",
        email="sarah@example.com",
        password_hash="x",
        first_name="Sarah",
        last_name="Lopez",
    )
    context = WorkspaceContext(
        company_id=str(employee.company_id),
        user_id=str(employee.id),
        role=Role.EMPLOYEE,
        workspace_type=None,
        workspace_id=None,
        data={"current_user": employee},
    )

    response = await compass.handle_message("What's my leave balance?", context)

    assert response.capability_used is None
    knowledge_service.ask.assert_not_awaited()
