"""
Connection strings from a host (Render, Neon, Heroku-style) are accepted as one DATABASE_URL and
translated into the two forms the application needs. See app/core/database_url.py.
"""

import pytest

from app.core.config import Settings
from app.core.database_url import to_async_url, to_sync_url


@pytest.mark.parametrize(
    "given",
    [
        "postgres://u:p@host:5432/db",
        "postgresql://u:p@host:5432/db",
        "postgresql+psycopg2://u:p@host:5432/db",
        "postgresql+asyncpg://u:p@host:5432/db",
    ],
)
def test_every_common_spelling_becomes_the_async_form(given: str) -> None:
    assert to_async_url(given) == "postgresql+asyncpg://u:p@host:5432/db"


def test_the_sync_form_is_for_migrations() -> None:
    assert to_sync_url("postgres://u:p@host/db") == "postgresql+psycopg2://u:p@host/db"


def test_ssl_is_spelled_the_way_each_driver_understands() -> None:
    # asyncpg rejects `sslmode`; psycopg2 rejects `ssl`.
    assert to_async_url("postgres://u:p@h/db?sslmode=require") == "postgresql+asyncpg://u:p@h/db?ssl=require"
    assert to_sync_url("postgres://u:p@h/db?ssl=require") == "postgresql+psycopg2://u:p@h/db?sslmode=require"


def test_other_query_parameters_and_special_characters_survive() -> None:
    assert (
        to_async_url("postgres://user:p%40ss@h:6543/db?sslmode=require&application_name=talign")
        == "postgresql+asyncpg://user:p%40ss@h:6543/db?ssl=require&application_name=talign"
    )


def test_something_that_is_not_postgres_is_left_alone() -> None:
    assert to_async_url("mysql://u:p@h/db") == "mysql://u:p@h/db"


def test_settings_derive_both_urls_from_one_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL_SYNC", raising=False)
    monkeypatch.setenv("DATABASE_URL", "postgres://u:p@dpg-abc/talign")

    settings = Settings(_env_file=None)

    assert settings.database_url == "postgresql+asyncpg://u:p@dpg-abc/talign"
    assert settings.database_url_sync == "postgresql+psycopg2://u:p@dpg-abc/talign"


def test_an_explicit_sync_url_is_kept(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgres://u:p@dpg-abc/talign")
    monkeypatch.setenv("DATABASE_URL_SYNC", "postgresql+psycopg2://m:q@other/mig")

    settings = Settings(_env_file=None)

    assert settings.database_url_sync == "postgresql+psycopg2://m:q@other/mig"


def test_the_defaults_are_untouched_when_nothing_is_set(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("DATABASE_URL_SYNC", raising=False)

    settings = Settings(_env_file=None)

    assert settings.database_url == "postgresql+asyncpg://talign:talign@localhost:5432/talign"
    assert settings.database_url_sync == "postgresql+psycopg2://talign:talign@localhost:5432/talign"


def test_parts_that_need_no_change_are_left_exactly_as_given() -> None:
    # A socket path in the query, and a percent-encoded password, must not be re-encoded.
    given = "postgres://u:p%40ss@/db?host=/var/run/postgresql&sslmode=require"
    assert to_async_url(given) == "postgresql+asyncpg://u:p%40ss@/db?host=/var/run/postgresql&ssl=require"


def test_a_neon_connection_string_works_as_pasted() -> None:
    # Neon's dashboard string: sslmode plus channel_binding. asyncpg rejects channel_binding.
    given = "postgresql://neondb_owner:secret@ep-cool-123.us-west-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
    assert to_async_url(given) == (
        "postgresql+asyncpg://neondb_owner:secret@ep-cool-123.us-west-2.aws.neon.tech/neondb?ssl=require"
    )
    # libpq (used by migrations) understands both options, so the sync form is left intact
    assert to_sync_url(given) == (
        "postgresql+psycopg2://neondb_owner:secret@ep-cool-123.us-west-2.aws.neon.tech/neondb"
        "?sslmode=require&channel_binding=require"
    )
