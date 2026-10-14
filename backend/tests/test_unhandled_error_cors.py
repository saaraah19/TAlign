"""
An unhandled backend exception must reach the browser as a readable 500.

Regression tests for a debugging trap: a crash in a route produced a 500
response with no CORS headers, so the browser reported "blocked by CORS
policy" and hid the real error (Sarah hit exactly this on /careers). The
earlier "fix" — an `@app.exception_handler(Exception)` — never worked,
because Starlette runs that handler outside the CORS middleware. See
app/core/error_middleware.py.

Each test builds a fresh app with `create_app()` and adds its own routes,
so nothing here touches the real routes or a database.
"""

from collections.abc import MutableMapping
from typing import Any

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from starlette.types import Message, Receive, Scope, Send

from app.core.error_middleware import UNEXPECTED_ERROR_MESSAGE, UnhandledExceptionMiddleware
from app.core.exceptions import ConflictError
from app.main import create_app

FRONTEND_ORIGIN = "http://localhost:3000"


@pytest.fixture
def app() -> FastAPI:
    test_app = create_app()

    @test_app.get("/__test/boom")
    async def boom() -> None:
        raise RuntimeError("simulated unhandled bug")

    @test_app.get("/__test/domain-error")
    async def domain_error() -> None:
        raise ConflictError("already exists")

    return test_app


async def _get(app: FastAPI, path: str, origin: str | None = FRONTEND_ORIGIN) -> Any:
    headers = {"Origin": origin} if origin else {}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        return await client.get(path, headers=headers)


async def test_unhandled_exception_returns_json_500(app: FastAPI) -> None:
    response = await _get(app, "/__test/boom")

    assert response.status_code == 500
    assert response.json() == {"detail": UNEXPECTED_ERROR_MESSAGE}


async def test_unhandled_exception_response_carries_cors_headers(app: FastAPI) -> None:
    # The whole point: without these headers the browser hides the 500.
    response = await _get(app, "/__test/boom")

    assert response.headers["access-control-allow-origin"] == FRONTEND_ORIGIN
    assert response.headers["access-control-allow-credentials"] == "true"


async def test_cors_still_refuses_an_unknown_origin_on_errors(app: FastAPI) -> None:
    response = await _get(app, "/__test/boom", origin="http://evil.example")

    assert response.status_code == 500
    assert "access-control-allow-origin" not in response.headers


async def test_domain_errors_keep_their_own_status_code(app: FastAPI) -> None:
    response = await _get(app, "/__test/domain-error")

    assert response.status_code == 409
    assert response.json() == {"detail": "already exists"}
    assert response.headers["access-control-allow-origin"] == FRONTEND_ORIGIN


async def test_ordinary_http_errors_are_not_turned_into_500s(app: FastAPI) -> None:
    response = await _get(app, "/__test/does-not-exist")

    assert response.status_code == 404


async def test_a_response_already_started_is_not_overwritten() -> None:
    # If headers are already sent, a clean 500 is impossible; the
    # middleware must re-raise rather than send a second response.
    sent: list[MutableMapping[str, Any]] = []

    async def half_sent_then_crash(scope: Scope, receive: Receive, send: Send) -> None:
        await send({"type": "http.response.start", "status": 200, "headers": []})
        raise RuntimeError("crashed mid-stream")

    async def collect(message: Message) -> None:
        sent.append(message)

    async def no_receive() -> Message:
        return {"type": "http.request", "body": b"", "more_body": False}

    middleware = UnhandledExceptionMiddleware(half_sent_then_crash)

    with pytest.raises(RuntimeError, match="crashed mid-stream"):
        await middleware({"type": "http", "path": "/x", "method": "GET"}, no_receive, collect)

    assert [m["type"] for m in sent] == ["http.response.start"]
