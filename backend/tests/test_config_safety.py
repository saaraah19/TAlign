"""
Configuration safety: a deployed instance must not start with development
defaults, and the browser-facing settings (CORS, cookies) must be
configurable rather than hard-coded.

`_env_file=None` keeps a developer's real .env from leaking into the tests.
"""

from types import SimpleNamespace
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError
from starlette.responses import Response

from app.api.v1.auth import REFRESH_COOKIE_NAME, SESSION_FLAG_COOKIE_NAME, _set_refresh_cookie
from app.core.config import Settings
from app.main import create_app

GOOD_SECRET = "x" * 48


def make(**overrides: Any) -> Settings:
    return Settings(_env_file=None, **overrides)  # type: ignore[call-arg]


# --- deployed environments refuse unsafe defaults -----------------------


@pytest.mark.parametrize("environment", ["staging", "production"])
def test_default_secret_is_refused_when_deployed(environment: str) -> None:
    with pytest.raises(ValidationError, match="JWT_SECRET_KEY"):
        make(environment=environment, debug=False)


@pytest.mark.parametrize("environment", ["staging", "production"])
def test_short_secret_is_refused_when_deployed(environment: str) -> None:
    with pytest.raises(ValidationError, match="at least 32 characters"):
        make(environment=environment, debug=False, jwt_secret_key="short")


@pytest.mark.parametrize("environment", ["staging", "production"])
def test_debug_is_refused_when_deployed(environment: str) -> None:
    with pytest.raises(ValidationError, match="DEBUG must be false"):
        make(environment=environment, debug=True, jwt_secret_key=GOOD_SECRET)


def test_every_problem_is_reported_at_once() -> None:
    with pytest.raises(ValidationError) as excinfo:
        make(environment="production", debug=True)
    message = str(excinfo.value)
    assert "JWT_SECRET_KEY" in message and "DEBUG" in message


@pytest.mark.parametrize("environment", ["staging", "production"])
def test_a_properly_configured_deployment_starts(environment: str) -> None:
    config = make(environment=environment, debug=False, jwt_secret_key=GOOD_SECRET)
    assert config.environment == environment


@pytest.mark.parametrize("environment", ["local", "test"])
def test_local_and_test_keep_their_convenient_defaults(environment: str) -> None:
    config = make(environment=environment)
    assert config.debug is True
    assert config.jwt_secret_key == "change-me-in-env"


# --- CORS origins -------------------------------------------------------


def test_cors_defaults_to_the_local_frontend() -> None:
    assert make().cors_origins_list == ["http://localhost:3000"]


def test_cors_accepts_several_origins_and_tidies_them() -> None:
    config = make(cors_origins=" https://app.example.com/ , http://localhost:3000 ,, ")
    assert config.cors_origins_list == ["https://app.example.com", "http://localhost:3000"]


def test_cors_wildcard_is_refused() -> None:
    with pytest.raises(ValidationError, match="cannot be '\\*'"):
        make(cors_origins="*")


def test_cors_entry_without_a_scheme_is_refused() -> None:
    with pytest.raises(ValidationError, match="http:// or https://"):
        make(cors_origins="app.example.com")


def test_cors_empty_value_is_refused() -> None:
    with pytest.raises(ValidationError, match="at least one origin"):
        make(cors_origins=" , ")


async def test_the_app_honours_the_configured_origins(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.main.settings", make(cors_origins="https://talign.example.com"))
    app = create_app()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        allowed = await client.get(
            "/api/v1/health", headers={"Origin": "https://talign.example.com"}
        )
        refused = await client.get("/api/v1/health", headers={"Origin": "http://localhost:3000"})

    assert allowed.headers["access-control-allow-origin"] == "https://talign.example.com"
    assert "access-control-allow-origin" not in refused.headers


# --- cookies ------------------------------------------------------------


def test_cookie_samesite_none_is_refused_locally() -> None:
    with pytest.raises(ValidationError, match="requires HTTPS"):
        make(environment="local", cookie_samesite="none")


def test_cookie_samesite_none_is_allowed_when_deployed() -> None:
    config = make(
        environment="production", debug=False, jwt_secret_key=GOOD_SECRET, cookie_samesite="none"
    )
    assert config.cookie_samesite == "none"


def _set_cookie_headers(monkeypatch: pytest.MonkeyPatch, config: Settings) -> list[str]:
    monkeypatch.setattr("app.api.v1.auth.settings", config)
    response = Response()
    _set_refresh_cookie(response, SimpleNamespace(refresh_token="token-value"))  # type: ignore[arg-type]
    return [v.decode() for k, v in response.raw_headers if k == b"set-cookie"]


def test_both_cookies_follow_the_configured_samesite(monkeypatch: pytest.MonkeyPatch) -> None:
    config = make(
        environment="production", debug=False, jwt_secret_key=GOOD_SECRET, cookie_samesite="none"
    )
    headers = _set_cookie_headers(monkeypatch, config)

    assert len(headers) == 2
    for header in headers:
        assert "SameSite=none" in header
        assert "Secure" in header  # SameSite=None is only valid on HTTPS cookies
    refresh = next(h for h in headers if h.startswith(REFRESH_COOKIE_NAME))
    assert "HttpOnly" in refresh
    session = next(h for h in headers if h.startswith(SESSION_FLAG_COOKIE_NAME))
    assert "HttpOnly" not in session


def test_local_cookies_stay_lax_and_not_secure(monkeypatch: pytest.MonkeyPatch) -> None:
    headers = _set_cookie_headers(monkeypatch, make())

    for header in headers:
        assert "SameSite=lax" in header
        assert "Secure" not in header
