"""
Auth-related FastAPI dependencies.

`get_current_user` re-fetches the user from the database on every
request (rather than trusting the JWT's embedded claims wholesale). This
costs one query per request but means a disabled account is rejected
immediately rather than staying valid until its access token naturally
expires — an acceptable trade-off at MVP scale, revisit if this becomes
a hot path.

`require_roles` is a dependency factory: `Depends(require_roles(Role.ADMIN))`
reads naturally at the route definition and keeps authorization checks
declarative rather than scattered as `if` statements inside handlers.
"""

import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import UserStatus
from app.core.exceptions import InvalidTokenError
from app.core.roles import Role
from app.core.security import TokenType, decode_token
from app.database.session import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository

_bearer_scheme = HTTPBearer(auto_error=True)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    try:
        payload = decode_token(credentials.credentials, expected_type=TokenType.ACCESS)
        user_id = uuid.UUID(payload["sub"])
    except (InvalidTokenError, ValueError, KeyError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    user = await UserRepository(db).get_by_id(user_id)
    if user is None or user.status != UserStatus.ACTIVE.value:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is inactive or no longer exists.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_roles(*allowed_roles: Role):
    """
    Usage: `Depends(require_roles(Role.ADMIN))` or
    `Depends(require_roles(Role.ADMIN, Role.RECRUITER))` for "any of".
    """
    allowed_names = {role.value for role in allowed_roles}

    async def _check(current_user: User = Depends(get_current_user)) -> User:
        if not allowed_names.intersection(current_user.roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action.",
            )
        return current_user

    return _check
