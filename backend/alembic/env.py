"""
Alembic environment.

Uses the SYNC database URL (`settings.database_url_sync`) even though the
app runs on an async engine at request time — Alembic's migration runner
is sync-only. This is the one place in the codebase allowed to use the
sync connection string.

Imports `Base.metadata` from app.database.base for autogenerate support.
As models are added (Slice 1+), they must be imported in
app/models/__init__.py so their tables register on this metadata —
otherwise `alembic revision --autogenerate` won't see them.
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import settings
from app.database.base import Base

# Slice 1+ populates app/models/__init__.py with model imports; importing
# it here (once it's non-empty) is what makes autogenerate see new tables.
import app.models  # noqa: F401,E402

config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url_sync)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
