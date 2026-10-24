"""
Tests for AuthService.convert_candidate_to_employee — the in-place
account conversion that gives a hired candidate a working employee
login. Same mocked-repository approach as test_auth_service_rules.py's
sibling files — no live database.
"""

import uuid
from unittest.mock import AsyncMock

from app.core.roles import Role as RoleEnum
from app.models.role import Role as RoleModel
from app.models.user import User
from app.services.auth_service import AuthService


def _candidate_user(user_id: uuid.UUID | None = None) -> User:
    return User(
        id=user_id or uuid.uuid4(),
        company_id=None,
        account_type="candidate",
        email="ahmed@example.com",
        password_hash="x",
        first_name="Ahmed",
        last_name="Benali",
    )


def _internal_user(user_id: uuid.UUID, company_id: uuid.UUID) -> User:
    return User(
        id=user_id,
        company_id=company_id,
        account_type="internal",
        email="ahmed@example.com",
        password_hash="x",
        first_name="Ahmed",
        last_name="Benali",
    )


def _make_service(*, existing_user: User | None):
    user_repo = AsyncMock()
    # First get_by_id call (pre-check) and the reload after commit both
    # need a return value; tests override .side_effect where the two
    # calls should differ (e.g. reload reflects the mutated row).
    user_repo.get_by_id.return_value = existing_user

    role_repo = AsyncMock()

    def _get_by_name(role: RoleEnum) -> RoleModel:
        return RoleModel(id=uuid.uuid4(), name=role.value)

    role_repo.get_by_name.side_effect = _get_by_name

    db = AsyncMock()
    service = AuthService(db, user_repository=user_repo, role_repository=role_repo)
    return service, user_repo, role_repo, db


async def test_converts_a_candidate_account_in_place() -> None:
    user_id = uuid.uuid4()
    company_id = uuid.uuid4()
    candidate = _candidate_user(user_id)
    service, user_repo, role_repo, db = _make_service(existing_user=candidate)

    user, converted = await service.convert_candidate_to_employee(
        user_id=user_id, company_id=company_id
    )

    assert converted is True
    assert candidate.account_type == "internal"
    assert candidate.company_id == company_id
    db.commit.assert_awaited_once()
    # Same row, same id — never a second account.
    assert user.id == user_id


async def test_grants_the_employee_role_and_removes_the_candidate_role() -> None:
    user_id = uuid.uuid4()
    company_id = uuid.uuid4()
    candidate = _candidate_user(user_id)
    service, user_repo, role_repo, _ = _make_service(existing_user=candidate)

    await service.convert_candidate_to_employee(user_id=user_id, company_id=company_id)

    # get_by_name was consulted for both roles — EMPLOYEE to grant, CANDIDATE to remove.
    requested_roles = [c.args[0] for c in role_repo.get_by_name.call_args_list]
    assert RoleEnum.EMPLOYEE in requested_roles
    assert RoleEnum.CANDIDATE in requested_roles
    user_repo.add_role.assert_awaited_once()
    user_repo.remove_role.assert_awaited_once()


async def test_is_idempotent_for_an_already_converted_account() -> None:
    user_id = uuid.uuid4()
    company_id = uuid.uuid4()
    already_internal = _internal_user(user_id, company_id)
    service, user_repo, role_repo, db = _make_service(existing_user=already_internal)

    user, converted = await service.convert_candidate_to_employee(
        user_id=user_id, company_id=company_id
    )

    assert converted is False
    assert user is already_internal
    user_repo.add_role.assert_not_awaited()
    user_repo.remove_role.assert_not_awaited()
    db.commit.assert_not_awaited()


async def test_scopes_the_account_to_exactly_the_hiring_company() -> None:
    """
    Confirmed MVP decision: an employee account belongs to exactly one
    company — the one that hired them, never any other.
    """
    user_id = uuid.uuid4()
    hiring_company = uuid.uuid4()
    other_company = uuid.uuid4()
    candidate = _candidate_user(user_id)
    service, *_rest = _make_service(existing_user=candidate)

    await service.convert_candidate_to_employee(user_id=user_id, company_id=hiring_company)

    assert candidate.company_id == hiring_company
    assert candidate.company_id != other_company
