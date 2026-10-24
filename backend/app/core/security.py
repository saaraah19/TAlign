"""
Security primitives: password hashing and JWT encode/decode.

RULE mirroring app/core/llm_provider.py: no other module imports
`passlib` or `jose` directly. Services depend on the functions here.

Token design:
  - Access token: short-lived (settings.access_token_expire_minutes),
    sent in the Authorization header, carries the claims the API needs
    on every request (user id, company, account type, roles) so
    `get_current_user` can authorize without hitting Role/UserRole
    tables on every single request — see app/api/deps.py for the
    trade-off notes on when it still re-fetches from the DB.
  - Refresh token: long-lived (settings.refresh_token_expire_days), sent
    ONLY as an httpOnly, Secure, SameSite cookie — never readable by
    frontend JS, which is the whole point (limits XSS blast radius to
    the short-lived access token only).
"""

import uuid
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.core.exceptions import InvalidTokenError

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    return _pwd_context.hash(plain_password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    return _pwd_context.verify(plain_password, password_hash)


class TokenType(StrEnum):
    ACCESS = "access"
    REFRESH = "refresh"


def _create_token(
    *,
    subject: str,
    token_type: TokenType,
    expires_delta: timedelta,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type.value,
        "iat": now,
        "exp": now + expires_delta,
        "jti": str(uuid.uuid4()),
        **(extra_claims or {}),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(
    *, user_id: uuid.UUID, company_id: uuid.UUID | None, account_type: str, roles: list[str]
) -> str:
    return _create_token(
        subject=str(user_id),
        token_type=TokenType.ACCESS,
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
        extra_claims={
            "company_id": str(company_id) if company_id else None,
            "account_type": account_type,
            "roles": roles,
        },
    )


def create_refresh_token(*, user_id: uuid.UUID) -> str:
    return _create_token(
        subject=str(user_id),
        token_type=TokenType.REFRESH,
        expires_delta=timedelta(days=settings.refresh_token_expire_days),
    )


def decode_token(token: str, *, expected_type: TokenType) -> dict[str, Any]:
    """
    Decode and validate a JWT.

    Raises `app.core.exceptions.InvalidTokenError` (not jose's JWTError)
    so callers only ever need to handle Talign's own exception hierarchy.
    """
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise InvalidTokenError("Token is invalid or expired.") from exc

    if payload.get("type") != expected_type.value:
        raise InvalidTokenError(f"Expected a {expected_type.value} token.")

    return payload
