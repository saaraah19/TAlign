"""
Role and UserRole models.

`Role` is a lookup table (seeded via migration data, see
alembic/versions/) rather than a Postgres native enum — adding a role in
a future version is a data insert, not an `ALTER TYPE` migration.
`app.core.roles.Role` (the Python StrEnum) is the source of truth for
which role *names* are valid; this table exists so roles are queryable,
joinable, and eventually extensible with per-role metadata.

`UserRole` is the join table enabling a user to hold multiple roles
(the Product Book's domain model explicitly calls this out — most users
will hold exactly one, but the schema doesn't assume that).
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    #: Matches a value of app.core.roles.Role exactly (validated at the
    #: service layer on write — see RoleRepository).
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)

    user_links: Mapped[list["UserRole"]] = relationship(back_populates="role")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Role name={self.name!r}>"


class UserRole(Base):
    __tablename__ = "user_roles"
    __table_args__ = (UniqueConstraint("user_id", "role_id", name="uq_user_roles_user_role"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="role_links")
    role: Mapped["Role"] = relationship(back_populates="user_links")
