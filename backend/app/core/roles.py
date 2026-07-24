"""
Role definitions.

This is the single canonical list of roles in Talign. It is imported by:
  - the `Role` / `UserRole` database models (Slice 1)
  - RBAC permission checks in the API layer (Slice 1)
  - Compass's capability registry, which scopes which AI capabilities a
    role may invoke (Slice 4+) — e.g. a Candidate role must never be able
    to reach "explain alignment score"

Keeping this in `core/` (rather than duplicating role strings across
modules) means the day we add a role, there's exactly one file to touch,
and every consumer (DB, API guards, Compass) reads from the same source.
"""

from enum import StrEnum


class Role(StrEnum):
    ADMIN = "admin"
    RECRUITER = "recruiter"
    HIRING_MANAGER = "hiring_manager"
    EMPLOYEE = "employee"
    CANDIDATE = "candidate"


# Roles that belong to the hiring organization, as opposed to external
# candidates. Used for coarse-grained checks (e.g. "internal notes are
# visible to INTERNAL_ROLES only") without listing every role by hand.
INTERNAL_ROLES: frozenset[Role] = frozenset(
    {Role.ADMIN, Role.RECRUITER, Role.HIRING_MANAGER, Role.EMPLOYEE}
)


class AccountType(StrEnum):
    """
    Coarse account dimension, distinct from `Role`.

    `Role` answers "what can this user do" (fine-grained RBAC, a user can
    hold several). `AccountType` answers "does this account belong to a
    company or to the platform itself" — exactly two values, and it's
    what the `users.company_id` database CHECK constraint keys off
    (see Slice 1 migration). Internal users (any role in INTERNAL_ROLES)
    are always INTERNAL; candidates are always CANDIDATE. Keeping this
    separate from Role means the DB constraint doesn't need to join
    against `user_roles` to enforce company-assignment rules.
    """

    INTERNAL = "internal"
    CANDIDATE = "candidate"


def account_type_for_role(role: Role) -> AccountType:
    """Single source of truth mapping a Role to its AccountType."""
    return AccountType.CANDIDATE if role is Role.CANDIDATE else AccountType.INTERNAL
