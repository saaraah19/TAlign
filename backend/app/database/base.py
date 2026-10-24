"""
Declarative base for all ORM models.

Every model in `app/models/` inherits from `Base`. Alembic's `env.py`
imports `Base.metadata` to autogenerate migrations — so any new model
module must be imported somewhere reachable from here (see
app/models/__init__.py, populated starting Slice 1) or Alembic won't see it.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
