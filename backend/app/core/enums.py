"""
Account-lifecycle enums.

Kept separate from `app/core/roles.py`: `Role` answers "what can this user
do" (RBAC), while `UserStatus` answers "is this account usable right now"
(lifecycle). Different concerns, different files, so a change to one
never risks touching the other.
"""

from enum import StrEnum


class UserStatus(StrEnum):
    ACTIVE = "active"
    INVITED = "invited"  # reserved for the future email-invite flow (not built in Slice 1)
    DISABLED = "disabled"
