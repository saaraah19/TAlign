"""
Application entrypoint.

Run locally with:  uvicorn app.main:app --reload
Run via Docker:     see docker-compose.yml (backend service)
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_v1_router
from app.compass.capabilities import register_default_capabilities
from app.core.config import settings
from app.core.exceptions import TalignError
from app.core.logging import configure_logging


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

    return app


app = create_app()
