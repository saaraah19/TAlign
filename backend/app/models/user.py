"""
User model.

Single `User` table for every human on the platform — admin, recruiter,
hiring manager, employee, candidate — per the Product Book's explicit
domain-model decision ("never split into RecruiterTable/EmployeeTable/
CandidateTable, it becomes a cauchemar"). What role(s) a user holds is
answered by `Role`/`UserRole`, not by which table the row lives in.

Company assignment rule (enforced at TWO layers, per instruction):
  - DB layer: the `ck_users_company_assignment` CHECK constraint below.
  - Service layer: AuthService validates this *before* attempting the
    insert, so violations surface as a clean domain error rather than a
    raw IntegrityError bubbling out of the database driver.

  Internal accounts (account_type=INTERNAL) MUST have a company_id.
  Candidate accounts (account_type=CANDIDATE) MUST NOT have a company_id
  — candidates are platform-wide identities; their relationship to any
  given company exists only through the (future) Application entity.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import UserStatus
from app.core.roles import AccountType
from app.database.base import Base

if TYPE_CHECKING:
    from app.models.company import Company
    from app.models.role import UserRole


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "(account_type = 'candidate' AND company_id IS NULL) "
            "OR (account_type = 'internal' AND company_id IS NOT NULL)",
            name="ck_users_company_assignment",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    #: NULL for candidates, required for every internal role. See module
    #: docstring — enforced by ck_users_company_assignment.
    company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=True
    )

    #: internal | candidate — see app.core.roles.AccountType. Distinct
    #: from Role: this is what the DB constraint keys off, so it doesn't
    #: need to join user_roles to enforce company-assignment rules.
    account_type: Mapped[AccountType] = mapped_column(String(20), nullable=False)

    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(512), nullable=True)

    status: Mapped[UserStatus] = mapped_column(
        String(20), nullable=False, default=UserStatus.ACTIVE
    )
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    company: Mapped["Company | None"] = relationship(back_populates="users")
    role_links: Mapped[list["UserRole"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    @property
    def roles(self) -> list[str]:
        """
        Convenience accessor — requires role_links to be eagerly loaded
        (see UserRepository, which always selectinloads this). Named
        `roles` (not `role_names`) so UserRead's `from_attributes=True`
        picks it up without a manual mapping step.
        """
        return [link.role.name for link in self.role_links]

    def __repr__(self) -> str:  # pragma: no cover
        return f"<User id={self.id} email={self.email!r} account_type={self.account_type}>"
