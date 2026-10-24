"""
Turns the connection string a host hands you into the two forms the application needs.

Hosts such as Render give a single URL that starts with `postgres://`. This application needs
two different spellings of it:

  * the ASYNC form (`postgresql+asyncpg://...`) for the running application, and
  * the SYNC form (`postgresql+psycopg2://...`) for Alembic migrations.

They also disagree about how SSL is requested: the URL convention (libpq, psycopg2) is
`?sslmode=require`, while asyncpg understands `?ssl=require` and rejects `sslmode`. These
helpers translate, so a deployment sets one DATABASE_URL and it works for both. They are pure
functions, with no settings and no I/O, so they are trivial to test.
"""

from __future__ import annotations

from urllib.parse import urlsplit, urlunsplit

_KNOWN_SCHEMES = ("postgres", "postgresql", "postgresql+asyncpg", "postgresql+psycopg2")


def _rewrite(url: str, *, scheme: str, rename: dict[str, str]) -> str:
    parts = urlsplit(url.strip())
    if parts.scheme not in _KNOWN_SCHEMES:
        return url  # not a PostgreSQL URL we understand: leave it alone and let the driver complain
    # Rename keys textually. Parsing and re-encoding the query would also rewrite characters that
    # were fine as they were (a socket path like host=/var/run/postgresql would become %2F...).
    pairs = []
    for pair in parts.query.split("&") if parts.query else []:
        key, sep, value = pair.partition("=")
        pairs.append(f"{rename.get(key, key)}{sep}{value}")
    return urlunsplit((scheme, parts.netloc, parts.path, "&".join(pairs), parts.fragment))


def to_async_url(url: str) -> str:
    """`postgres://u:p@h/db?sslmode=require` -> `postgresql+asyncpg://u:p@h/db?ssl=require`."""
    return _rewrite(url, scheme="postgresql+asyncpg", rename={"sslmode": "ssl"})


def to_sync_url(url: str) -> str:
    """`postgres://u:p@h/db?ssl=require` -> `postgresql+psycopg2://u:p@h/db?sslmode=require`."""
    return _rewrite(url, scheme="postgresql+psycopg2", rename={"ssl": "sslmode"})
