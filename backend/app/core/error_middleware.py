"""
Last-resort handling of unhandled exceptions, placed where CORS can see it.

The problem this solves: a genuinely unhandled exception (anything that is
not a `TalignError` or an `HTTPException` — a bug, a failed validation of
a response model, a lost database connection) used to produce a 500
response with NO CORS headers. The browser then refuses to hand that
response to the page and reports a CORS failure, hiding the real error:
the console says "blocked by CORS policy" while the actual cause is a
crash in the backend logs.

Why `@app.exception_handler(Exception)` does not fix it (an earlier
version of this codebase relied on that, wrongly): Starlette routes
handlers registered for `Exception` / 500 to its `ServerErrorMiddleware`,
which is always the OUTERMOST layer — outside `CORSMiddleware` — so the
response it produces never passes back through CORS. And while
`debug=True` (the local default) it is bypassed altogether in favour of
Starlette's debug traceback page.

The fix is to turn the exception into a response one layer further IN.
This middleware is registered before `CORSMiddleware` (see
app/main.py), which puts it inside it: it catches the exception, returns
a JSON 500, and that response travels outward through CORS and picks up
the headers on the way. `TalignError` and `HTTPException` are handled
even further in, by Starlette's own exception middleware, so they never
reach this code and keep their status codes.

Written as plain ASGI rather than `BaseHTTPMiddleware`, which wraps
responses in ways that interfere with streaming and background tasks.
"""

import structlog
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

logger = structlog.get_logger(__name__)

UNEXPECTED_ERROR_MESSAGE = "An unexpected error occurred. This has been logged."


class UnhandledExceptionMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        response_started = False

        async def tracking_send(message: Message) -> None:
            nonlocal response_started
            if message["type"] == "http.response.start":
                response_started = True
            await send(message)

        try:
            await self.app(scope, receive, tracking_send)
        except Exception:
            logger.exception(
                "unhandled_exception",
                path=scope.get("path"),
                method=scope.get("method"),
            )
            if response_started:
                # Headers and part of the body are already on the wire,
                # so a clean 500 is no longer possible. Let Starlette's
                # outer layer deal with it (it closes the connection).
                raise
            response = JSONResponse(
                status_code=500,
                content={"detail": UNEXPECTED_ERROR_MESSAGE},
            )
            await response(scope, receive, send)
