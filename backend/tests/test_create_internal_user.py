"""
`AuthService.create_internal_user`: adding staff to the acting admin's company.

Regression: against a real database this endpoint returned a 500 for every
call. The service committed, which expires the new user object, and the
route then read `user.roles` — a lazy relationship that async SQLAlchemy
cannot load on demand (MissingGreenlet). Mocked tests could never show it.
The contract that prevents it, tested here, is: after committing, the
service hands back a user RELOADED through the repository (whose read
methods eager-load roles), never the stale instance it created.
"""

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.core.exceptions import EmailAlreadyExistsError, InvalidCompanyAssignmentError
from app.core.roles import Role
from app.services.auth_service import AuthService

COMPANY_ID = uuid.uuid4()


def _service() -> tuple[AuthService, list[str], SimpleNamespace, SimpleNamespace]:
    """An AuthService whose collaborators record the order they are used in."""
    calls: list[str] = []
    stale = SimpleNamespace(id=uuid.uuid4(), name="the instance expired by commit")
    reloaded = SimpleNamespace(id=stale.id, name="the instance reloaded with its roles")

    db = AsyncMock()

    async def commit() -> None:
        calls.append("commit")

    db.commit = commit

    users = AsyncMock()
    users.email_exists.return_value = False

    async def get_by_id(user_id: uuid.UUID) -> SimpleNamespace:
        calls.append("reload")
        assert user_id == stale.id
        return reloaded

    users.get_by_id = get_by_id

    service = AuthService(db, user_repository=users)
    service._register_user = AsyncMock(return_value=stale)  # type: ignore[method-assign]
    return service, calls, stale, reloaded


async def _create(service: AuthService, role: Role = Role.RECRUITER) -> object:
    return await service.create_internal_user(
        email="emma@example.com",
        password="Password123!",
        first_name="Emma",
        last_name="Martin",
        role=role,
        acting_company_id=COMPANY_ID,
    )


async def test_returns_the_reloaded_user_not_the_expired_instance() -> None:
    service, _, stale, reloaded = _service()

    result = await _create(service)

    assert result is reloaded
    assert result is not stale


async def test_reloads_only_after_committing() -> None:
    service, calls, _, _ = _service()

    await _create(service)

    assert calls == ["commit", "reload"]


async def test_creates_the_user_in_the_acting_admins_company() -> None:
    service, _, _, _ = _service()

    await _create(service, Role.HIRING_MANAGER)

    kwargs = service._register_user.await_args.kwargs  # type: ignore[attr-defined]
    assert kwargs["company_id"] == COMPANY_ID
    assert kwargs["role"] is Role.HIRING_MANAGER


async def test_refuses_to_create_a_candidate_this_way() -> None:
    service, calls, _, _ = _service()

    with pytest.raises(InvalidCompanyAssignmentError):
        await _create(service, Role.CANDIDATE)

    assert calls == []  # nothing was committed


async def test_refuses_an_email_that_is_already_taken() -> None:
    service, calls, _, _ = _service()
    service._users.email_exists.return_value = True  # type: ignore[attr-defined]

    with pytest.raises(EmailAlreadyExistsError):
        await _create(service)

    assert calls == []
