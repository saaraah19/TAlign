"""
Auth endpoints.

Thin by design — every handler does three things: extract input, call
AuthService, shape the response. No business logic lives here (mirrors
the same rule now formalized for Compass: routing/plumbing only).

Refresh token cookie settings:
  httponly=True   — never readable by frontend JS (XSS mitigation)
  secure=True      — HTTPS only; disabled automatically in local dev via
                      settings.environment so http://localhost still works
  samesite="lax"   — sent on top-level navigation, blocks most CSRF
                      vectors for a cookie that only matters on same-site
                      API calls
"""

import uuid

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_roles
from app.core.config import settings
from app.core.exceptions import DomainValidationError
from app.core.roles import Role
from app.database.session import get_db
from app.models.user import User
from app.schemas.auth import (
    AccessTokenResponse,
    CreateInternalUserRequest,
    LoginRequest,
    RegisterCandidateRequest,
    RegisterCompanyRequest,
    TokenResponse,
)
from app.schemas.user import UserRead
from app.services.auth_service import AuthService, TokenPair

router = APIRouter()

REFRESH_COOKIE_NAME = "talign_refresh_token"
#: Non-httpOnly, non-sensitive. Exists ONLY so Next.js edge middleware can
#: redirect unauthenticated visitors away from protected pages without a
#: round-trip. It is NOT a security boundary — the refresh cookie above
#: (httpOnly, narrow path) and the bearer-token check in get_current_user
#: are what actually gate access. Losing or forging this cookie only
#: costs a redirect, never real authorization.
SESSION_FLAG_COOKIE_NAME = "talign_session"


def _set_refresh_cookie(response: Response, token_pair: TokenPair) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=token_pair.refresh_token,
        httponly=True,
        secure=settings.environment != "local",
        samesite="lax",
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
        path="/api/v1/auth",
    )
    response.set_cookie(
        key=SESSION_FLAG_COOKIE_NAME,
        value="1",
        httponly=False,
        secure=settings.environment != "local",
        samesite="lax",
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
        path="/",
    )


@router.post("/register/company", response_model=TokenResponse, status_code=201)
async def register_company(
    payload: RegisterCompanyRequest, response: Response, db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    user, tokens = await AuthService(db).register_company(payload)
    _set_refresh_cookie(response, tokens)
    return TokenResponse(
        access_token=tokens.access_token,
        expires_in=tokens.expires_in,
        user=UserRead.model_validate(user),
    )


@router.post("/register/candidate", response_model=TokenResponse, status_code=201)
async def register_candidate(
    payload: RegisterCandidateRequest, response: Response, db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    user, tokens = await AuthService(db).register_candidate(payload)
    _set_refresh_cookie(response, tokens)
    return TokenResponse(
        access_token=tokens.access_token,
        expires_in=tokens.expires_in,
        user=UserRead.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    user, tokens = await AuthService(db).authenticate(payload.email, payload.password)
    _set_refresh_cookie(response, tokens)
    return TokenResponse(
        access_token=tokens.access_token,
        expires_in=tokens.expires_in,
        user=UserRead.model_validate(user),
    )


@router.post("/refresh", response_model=AccessTokenResponse)
async def refresh(
    response: Response,
    db: AsyncSession = Depends(get_db),
    refresh_token: str | None = Cookie(default=None, alias=REFRESH_COOKIE_NAME),
) -> AccessTokenResponse:
    if refresh_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="No refresh token provided."
        )

    tokens = await AuthService(db).refresh(refresh_token)
    _set_refresh_cookie(response, tokens)  # rotate the refresh token on every use
    return AccessTokenResponse(access_token=tokens.access_token, expires_in=tokens.expires_in)


@router.post("/logout", status_code=204)
async def logout(response: Response) -> None:
    response.delete_cookie(key=REFRESH_COOKIE_NAME, path="/api/v1/auth")
    response.delete_cookie(key=SESSION_FLAG_COOKIE_NAME, path="/")


@router.get("/me", response_model=UserRead)
async def me(current_user: User = Depends(get_current_user)) -> UserRead:
    return UserRead.model_validate(current_user)


@router.post("/internal-users", response_model=UserRead, status_code=201)
async def create_internal_user(
    payload: CreateInternalUserRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(Role.ADMIN)),
) -> UserRead:
    try:
        role = Role(payload.role)
    except ValueError:
        raise DomainValidationError(f"Unknown role '{payload.role}'.") from None

    user = await AuthService(db).create_internal_user(
        email=payload.email,
        password=payload.password,
        first_name=payload.first_name,
        last_name=payload.last_name,
        role=role,
        acting_company_id=current_user.company_id,  # type: ignore[arg-type]
    )
    return UserRead.model_validate(user)
