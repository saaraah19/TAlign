"""
Auth flow schemas.

Password rule (min 8 chars) is intentionally duplicated in the frontend's
Zod schema (features/auth/types.ts) — client-side validation is UX only,
never a security boundary; the backend is the source of truth.
"""

from pydantic import BaseModel, EmailStr, Field

from app.schemas.user import UserRead


class RegisterCompanyRequest(BaseModel):
    company_name: str = Field(min_length=2, max_length=255)
    admin_first_name: str = Field(min_length=1, max_length=100)
    admin_last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class RegisterCandidateRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class CreateInternalUserRequest(BaseModel):
    """
    Admin-only endpoint for adding a recruiter/hiring_manager/employee/
    admin directly to their own company.

    Deliberately simple for Slice 1: the admin sets an initial password
    and shares it out-of-band. A token-based email invite (Product
    Book's "HR Director invites Recruiter" flow) is deferred — see
    docs/01_slice1_authentication.md — since it depends on the
    Communication Agent infrastructure that doesn't exist yet.
    """

    email: EmailStr
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    role: str  # validated against app.core.roles.Role, excluding CANDIDATE
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    user: UserRead


class AccessTokenResponse(BaseModel):
    """Returned by /auth/refresh — only the access token rotates in the response body; the new refresh token is set as a cookie."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
