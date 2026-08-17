"""
Application configuration.

Single source of truth for environment-driven settings. Nothing in the
codebase should read `os.environ` directly outside this module — every
other module imports `settings` from here.

Why this matters architecturally: it means swapping environments (local,
CI, staging) is a matter of swapping the `.env` file, never editing code.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- App ---
    app_name: str = "Talign"
    environment: Literal["local", "test", "staging", "production"] = "local"
    debug: bool = True
    api_v1_prefix: str = "/api/v1"

    # --- Database ---
    database_url: str = Field(
        default="postgresql+asyncpg://talign:talign@localhost:5432/talign",
        description="Async SQLAlchemy connection string.",
    )
    database_url_sync: str = Field(
        default="postgresql+psycopg2://talign:talign@localhost:5432/talign",
        description="Sync connection string, used by Alembic migrations only.",
    )

    # --- Auth (wired in Slice 1, declared here so config shape is stable) ---
    jwt_secret_key: str = Field(default="change-me-in-env")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 14

    # --- LLM Provider ---
    # Talign defaults to Gemini but the app must never import the Gemini SDK
    # directly outside app/core/llm_provider.py. See LLMProvider protocol.
    llm_provider: Literal["gemini", "openai", "anthropic"] = "gemini"
    google_api_key: str | None = None
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    llm_default_model: str = "gemini-2.5-flash"

    # --- Storage ---
    # MVP uses local disk. StorageProvider abstraction (Slice 1+) will let
    # this become "s3" / "supabase" without touching calling code.
    storage_provider: Literal["local"] = "local"
    local_storage_path: str = "./storage"

    # --- Document uploads (Slice 4: resumes; Slice 6: knowledge documents) ---
    # Configurable rather than hardcoded per explicit instruction — a
    # recruiter/admin-tunable limit, not a constant buried in code.
    # Content types are shared (resumes and knowledge documents accept
    # the same formats); file size limits stay separate — a company
    # policy document is reasonably expected to run larger than a resume.
    max_resume_file_size_bytes: int = 5 * 1024 * 1024  # 5 MB
    max_knowledge_file_size_bytes: int = 20 * 1024 * 1024  # 20 MB
    allowed_document_content_types: list[str] = Field(
        default_factory=lambda: [
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # .docx
            "text/plain",
        ]
    )

    # --- Knowledge Agent (Slice 6) ---
    knowledge_retrieval_top_k: int = 5

    # --- Logging ---
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    log_json: bool = False  # True in staging/production for structured logs


@lru_cache
def get_settings() -> Settings:
    """
    Cached settings accessor.

    Using a function (rather than a module-level `settings = Settings()`)
    means tests can override env vars and call `get_settings.cache_clear()`
    without fighting import-time singletons.
    """
    return Settings()


settings = get_settings()
