"""
The throttle as a client experiences it: the real /auth/login route,
with only the database session and the password check replaced.
"""

import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.exceptions import InvalidCredentialsError
from app.core.login_rate_limiter import login_limiter
from app.database.session import get_db
from app.main import app
from app.services.auth_service import AuthService

CREDENTIALS = {"email": "sam@example.com", "password": "whatever-1234"}


@pytest.fixture
def password_is_correct() -> dict[str, bool]:
    return {"value": False}


@pytest.fixture
async def client(
    monkeypatch: pytest.MonkeyPatch, password_is_correct: dict[str, bool]
) -> AsyncIterator[AsyncClient]:
    async def fake_db() -> AsyncIterator[None]:
        yield None

    async def fake_authenticate(self: AuthService, email: str, password: str) -> Any:
        if not password_is_correct["value"]:
            raise InvalidCredentialsError("Invalid email or password.")
        # Every field UserRead reads, so the real response model validates it.
        user = SimpleNamespace(
            id=uuid.uuid4(),
            company_id=None,
            account_type="candidate",
            email=email,
            first_name="Sam",
            last_name="Q",
            avatar_url=None,
            status="active",
            roles=["candidate"],
            created_at=datetime(2026, 10, 10, tzinfo=UTC),
        )
        tokens = SimpleNamespace(access_token="a", refresh_token="r", expires_in=1800)
        return user, tokens

    monkeypatch.setattr(AuthService, "authenticate", fake_authenticate)
    app.dependency_overrides[get_db] = fake_db
    login_limiter.clear()
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            yield c
    finally:
        app.dependency_overrides.pop(get_db, None)
        login_limiter.clear()


async def _login(client: AsyncClient, **overrides: str) -> Any:
    return await client.post("/api/v1/auth/login", json={**CREDENTIALS, **overrides})


async def test_wrong_passwords_are_refused_normally_at_first(client: AsyncClient) -> None:
    response = await _login(client)

    assert response.status_code == 401


async def test_repeated_wrong_passwords_lock_the_account_out_with_a_429(
    client: AsyncClient,
) -> None:
    limit = login_limiter._max_failures
    for _ in range(limit):
        assert (await _login(client)).status_code == 401

    response = await _login(client)

    assert response.status_code == 429
    assert "Too many failed sign-in attempts" in response.json()["detail"]
    assert int(response.headers["retry-after"]) > 0


async def test_the_lockout_holds_even_for_the_right_password(
    client: AsyncClient, password_is_correct: dict[str, bool]
) -> None:
    for _ in range(login_limiter._max_failures):
        await _login(client)

    password_is_correct["value"] = True
    response = await _login(client)

    assert response.status_code == 429  # otherwise guessing could simply continue


async def test_the_429_still_carries_cors_headers_so_the_browser_shows_the_message(
    client: AsyncClient,
) -> None:
    for _ in range(login_limiter._max_failures):
        await _login(client)

    response = await client.post(
        "/api/v1/auth/login", json=CREDENTIALS, headers={"Origin": "http://localhost:3000"}
    )

    assert response.status_code == 429
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"


async def test_a_different_email_is_not_affected(client: AsyncClient) -> None:
    for _ in range(login_limiter._max_failures):
        await _login(client)

    response = await _login(client, email="someone-else@example.com")

    assert response.status_code == 401  # a normal failure, not a lockout


async def test_a_successful_login_resets_the_count(
    client: AsyncClient, password_is_correct: dict[str, bool]
) -> None:
    for _ in range(login_limiter._max_failures - 1):
        await _login(client)
    password_is_correct["value"] = True
    assert (await _login(client)).status_code == 200

    password_is_correct["value"] = False
    for _ in range(login_limiter._max_failures - 1):
        assert (await _login(client)).status_code == 401  # count started again from zero
