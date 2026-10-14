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

from pydantic import Field, field_validator, model_validator
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

    # --- Browser access (CORS) ---
    # Comma-separated list of the exact origins (scheme + host + port, no
    # trailing slash) that may call this API from a browser, e.g.
    # "https://talign.onrender.com". It used to be hard-coded to
    # localhost:3000, which made any real deployment fail until the code
    # was edited. Read it through `cors_origins_list`.
    cors_origins: str = Field(default="http://localhost:3000")

    # --- Auth (wired in Slice 1, declared here so config shape is stable) ---
    jwt_secret_key: str = Field(default="change-me-in-env")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 14

    # SameSite attribute of the refresh/session cookies. "lax" is right when
    # the frontend and the API share a site (always the case on localhost,
    # or behind one domain / a reverse proxy). If they are on DIFFERENT
    # sites — e.g. two separate *.onrender.com services, which browsers
    # treat as cross-site — a "lax" cookie is silently dropped on the API
    # calls and nobody stays logged in; set COOKIE_SAMESITE=none there.
    # "none" requires HTTPS, so it is refused when ENVIRONMENT=local.
    cookie_samesite: Literal["lax", "strict", "none"] = "lax"

    # Failed-login throttling (see app/core/login_rate_limiter.py).
    login_max_failed_attempts: int = Field(default=5, ge=1)
    login_lockout_window_seconds: int = Field(default=15 * 60, ge=1)

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


    @field_validator("cors_origins")
    @classmethod
    def _normalise_cors_origins(cls, value: str) -> str:
        origins = [o.strip().rstrip("/") for o in value.split(",") if o.strip()]
        if not origins:
            raise ValueError("CORS_ORIGINS must list at least one origin.")
        for origin in origins:
            if origin == "*":
                # The API sets credentials (cookies); browsers reject a
                # wildcard origin combined with credentials, and it would
                # be unsafe if they didn't.
                raise ValueError("CORS_ORIGINS cannot be '*': list the exact origins instead.")
            if not origin.startswith(("http://", "https://")):
                raise ValueError(
                    f"CORS_ORIGINS entry {origin!r} must start with http:// or https://."
                )
        return ",".join(origins)

    @model_validator(mode="after")
    def _refuse_unsafe_deployed_settings(self) -> "Settings":
        """
        Fail at startup, loudly, rather than run a deployed instance with
        development defaults. `local` and `test` are exempt.
        """
        if self.cookie_samesite == "none" and self.environment == "local":
            raise ValueError(
                "COOKIE_SAMESITE=none requires HTTPS, so it cannot be used with "
                "ENVIRONMENT=local. Use 'lax' locally."
            )

        if self.environment in ("staging", "production"):
            problems: list[str] = []
            if self.jwt_secret_key == "change-me-in-env" or len(self.jwt_secret_key) < 32:
                problems.append(
                    "JWT_SECRET_KEY must be a random value of at least 32 characters "
                    "(anyone who knows the default can forge login tokens)"
                )
            if self.debug:
                problems.append("DEBUG must be false (it exposes internals in error pages)")
            if problems:
                raise ValueError(
                    f"Unsafe configuration for ENVIRONMENT={self.environment}: "
                    + "; ".join(problems)
                    + "."
                )
        return self

    @property
    def cors_origins_list(self) -> list[str]:
        return self.cors_origins.split(",")


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
