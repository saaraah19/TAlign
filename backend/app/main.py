"""
Application entrypoint.

Run locally with:  uvicorn app.main:app --reload
Run via Docker:     see docker-compose.yml (backend service)
"""

from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_v1_router
from app.compass.capabilities import register_default_capabilities
from app.core.config import settings
from app.core.exceptions import TalignError
from app.core.logging import configure_logging

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    # Registers concrete Agents + their Compass capabilities exactly
    # once, at startup — see app/compass/capabilities.py. Everything
    # downstream (Compass routing, the Agent Registry) assumes this has
    # already run by the time the first request arrives.
    register_default_capabilities()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_v1_router, prefix=settings.api_v1_prefix)

    @app.exception_handler(TalignError)
    async def talign_error_handler(request: Request, exc: TalignError) -> JSONResponse:
        # Single translation point from domain exceptions (raised by
        # services, never by the API layer) to HTTP responses. Services
        # stay unaware that FastAPI/HTTP exists at all.
        return JSONResponse(status_code=exc.http_status, content={"detail": exc.message})

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        # Defense in depth, not a substitute for fixing real bugs.
        #
        # Without this, a genuinely unhandled exception (anything not a
        # TalignError — e.g. the MissingGreenlet/expired-attribute bug
        # this was written to catch, or any future one like it) falls
        # through to Starlette's default ServerErrorMiddleware, which
        # sits OUTSIDE the CORSMiddleware added via app.add_middleware()
        # above. That means the resulting 500 response never gets CORS
        # headers attached, so the browser rejects it as a cross-origin
        # violation before the frontend ever sees a status code — it
        # shows up in JS as a bare `TypeError: Failed to fetch`, not a
        # catchable ApiError, making it look like a network problem
        # instead of the real backend crash it actually is.
        #
        # Registering the handler here (via @app.exception_handler, on
        # the FastAPI app itself) means it's processed by FastAPI's own
        # routing-level exception handling, which IS wrapped by
        # CORSMiddleware — so the response correctly carries CORS
        # headers and the frontend gets a normal, catchable ApiError.
        logger.exception("unhandled_exception", path=request.url.path, method=request.method)
        return JSONResponse(
            status_code=500,
            content={"detail": "An unexpected error occurred. This has been logged."},
        )

    return app


app = create_app()
