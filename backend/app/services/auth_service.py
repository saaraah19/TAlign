"""
AuthService.

Owns every business rule around account creation and authentication.
This is domain-service territory per the layering rule: Compass never
lands here, the API layer never lands here — it only calls in.

Company-assignment enforcement (service-layer half; DB half is the
ck_users_company_assignment CHECK constraint on `users`):
  - `_register_user` is the single choke point every registration path
    goes through. It derives `account_type` from the role being granted
    and raises `InvalidCompanyAssignmentError` if the caller's
    company_id doesn't match what that account_type requires. No
    registration path can bypass this by calling the repository
    directly — repositories have no rule-checking of their own.
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.enums import UserStatus
from app.core.exceptions import (
    EmailAlreadyExistsError,
    InactiveAccountError,
    InvalidCompanyAssignmentError,
    InvalidCredentialsError,
    InvalidTokenError,
)
from app.core.roles import AccountType, account_type_for_role
from app.core.roles import Role as RoleEnum
from app.core.security import (
    TokenType,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.company import Company
from app.models.user import User
from app.repositories.company_repository import CompanyRepository
from app.repositories.role_repository import RoleRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import RegisterCandidateRequest, RegisterCompanyRequest
from app.utils.slugify import slugify


class TokenPair:
    def __init__(self, access_token: str, refresh_token: str, expires_in: int) -> None:
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.expires_in = expires_in


class AuthService:
    def __init__(
        self,
        db: AsyncSession,
        user_repository: UserRepository | None = None,
        company_repository: CompanyRepository | None = None,
        role_repository: RoleRepository | None = None,
    ) -> None:
        self._db = db
        self._users = user_repository or UserRepository(db)
        self._companies = company_repository or CompanyRepository(db)
        self._roles = role_repository or RoleRepository(db)

    # --- Registration ---

    async def register_company(self, payload: RegisterCompanyRequest) -> tuple[User, TokenPair]:
        """Creates a new Company plus its first user, who is granted ADMIN."""
        if await self._users.email_exists(payload.email):
            raise EmailAlreadyExistsError("An account with this email already exists.")

        slug = await self._unique_slug(payload.company_name)
        company = await self._companies.create(Company(name=payload.company_name, slug=slug))

        user = await self._register_user(
            email=payload.email,
            password=payload.password,
            first_name=payload.admin_first_name,
            last_name=payload.admin_last_name,
            role=RoleEnum.ADMIN,
            company_id=company.id,
        )
        await self._db.commit()
        return await self._reload_with_tokens(user.id)

    async def register_candidate(
        self, payload: RegisterCandidateRequest
    ) -> tuple[User, TokenPair]:
        """Creates a platform-wide Candidate account — never company-scoped."""
        if await self._users.email_exists(payload.email):
            raise EmailAlreadyExistsError("An account with this email already exists.")

        user = await self._register_user(
            email=payload.email,
            password=payload.password,
            first_name=payload.first_name,
            last_name=payload.last_name,
            role=RoleEnum.CANDIDATE,
            company_id=None,
        )
        await self._db.commit()
        return await self._reload_with_tokens(user.id)

    async def create_internal_user(
        self,
        *,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        role: RoleEnum,
        acting_company_id: uuid.UUID,
    ) -> User:
        """
        Admin-only: adds a recruiter/hiring_manager/employee/admin to the
        ACTING admin's own company. `acting_company_id` comes from the
        authenticated caller's token, never from the request body — an
        admin cannot create users in a company they don't belong to.
        """
        if role is RoleEnum.CANDIDATE:
            raise InvalidCompanyAssignmentError(
                "Candidates cannot be created via the internal-user endpoint; "
                "use candidate self-registration."
            )
        if await self._users.email_exists(email):
            raise EmailAlreadyExistsError("An account with this email already exists.")

        user = await self._register_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role=role,
            company_id=acting_company_id,
        )
        await self._db.commit()
        return user

    async def convert_candidate_to_employee(
        self, *, user_id: uuid.UUID, company_id: uuid.UUID
    ) -> tuple[User, bool]:
        """
        Converts an existing candidate account into a company-scoped
        employee account, IN PLACE — same login, same password, same
        row. Called once, by HireCandidateWorkflow, when a candidate is
        hired.

        This is a conversion rather than creating a new account because
        there is no separate Candidate identity in this codebase to
        link against: `Application.candidate_id` already points at a
        User row with account_type=CANDIDATE (see application.py's
        module docstring). A second account with the same email
        couldn't be created anyway — email is globally unique — so
        there is genuinely nothing to create here, only three fields on
        the existing row to flip: account_type, company_id, and role.

        Confirmed MVP scope: an employee account is scoped to exactly
        one company, same as every other internal account_type. Once
        converted, this login can no longer apply as a platform-wide
        candidate elsewhere on Talign — what matters once someone is
        hired is which company hired them, not how many they'd applied
        to before that point. Not handling "un-hire back to candidate"
        or multi-company employment is a deliberate MVP limitation, not
        an oversight.

        Idempotent: returns (user, False) without modifying anything if
        the account was already converted (a second hire-workflow
        trigger for the same application) rather than attempting to
        convert an already-internal account a second time.
        """
        user = await self._users.get_by_id(user_id)
        if user is None:
            # The candidate row backing an Application should always
            # exist (FK-guaranteed) — this is a defensive guard against
            # a genuinely inconsistent state, not an expected path.
            raise RuntimeError(f"User '{user_id}' not found during hire conversion.")

        if user.account_type == AccountType.INTERNAL.value:
            return user, False

        employee_role = await self._roles.get_by_name(RoleEnum.EMPLOYEE)
        if employee_role is None:
            raise RuntimeError("Role 'employee' is not seeded in the database.")
        candidate_role = await self._roles.get_by_name(RoleEnum.CANDIDATE)

        user.account_type = account_type_for_role(RoleEnum.EMPLOYEE)
        user.company_id = company_id
        await self._users.add_role(user.id, employee_role.id)
        if candidate_role is not None:
            await self._users.remove_role(user.id, candidate_role.id)

        await self._db.commit()
        converted = await self._users.get_by_id(user.id)  # reload, roles eager-loaded fresh
        assert converted is not None
        return converted, True

    async def _register_user(
        self,
        *,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        role: RoleEnum,
        company_id: uuid.UUID | None,
    ) -> User:
        """
        Single choke point for account creation. Every public
        registration method above routes through here — this is what
        makes the company-assignment rule impossible to bypass from
        within the service layer.
        """
        account_type = account_type_for_role(role)
        self._assert_company_assignment_valid(account_type=account_type, company_id=company_id)

        role_row = await self._roles.get_by_name(role)
        if role_row is None:
            # Indicates the Slice 1 seed migration wasn't run — a setup
            # error, not a user-facing one, so we let this raise as a
            # plain exception rather than a domain error.
            raise RuntimeError(f"Role '{role.value}' is not seeded in the database.")

        user = User(
            company_id=company_id,
            account_type=account_type.value,
            email=email.lower(),
            password_hash=hash_password(password),
            first_name=first_name,
            last_name=last_name,
            status=UserStatus.ACTIVE.value,
        )
        user = await self._users.create(user)
        await self._users.add_role(user.id, role_row.id)
        return user

    @staticmethod
    def _assert_company_assignment_valid(
        *, account_type: AccountType, company_id: uuid.UUID | None
    ) -> None:
        if account_type is AccountType.CANDIDATE and company_id is not None:
            raise InvalidCompanyAssignmentError(
                "Candidate accounts must not be associated with a company."
            )
        if account_type is AccountType.INTERNAL and company_id is None:
            raise InvalidCompanyAssignmentError(
                "Internal accounts (admin, recruiter, hiring manager, employee) "
                "must belong to exactly one company."
            )

    async def _unique_slug(self, company_name: str) -> str:
        base_slug = slugify(company_name) or "company"
        slug = base_slug
        suffix = 1
        while await self._companies.slug_exists(slug):
            suffix += 1
            slug = f"{base_slug}-{suffix}"
        return slug

    # --- Authentication ---

    async def authenticate(self, email: str, password: str) -> tuple[User, TokenPair]:
        user = await self._users.get_by_email(email)
        if user is None or not verify_password(password, user.password_hash):
            raise InvalidCredentialsError("Incorrect email or password.")
        if user.status != UserStatus.ACTIVE.value:
            raise InactiveAccountError("This account is not active.")

        return await self._reload_with_tokens(user.id)

    async def refresh(self, refresh_token: str) -> TokenPair:
        payload = decode_token(refresh_token, expected_type=TokenType.REFRESH)
        user = await self._users.get_by_id(uuid.UUID(payload["sub"]))
        if user is None or user.status != UserStatus.ACTIVE.value:
            raise InvalidTokenError("Refresh token no longer maps to an active account.")

        return self._issue_tokens(user)

    def _issue_tokens(self, user: User) -> TokenPair:
        access_token = create_access_token(
            user_id=user.id,
            company_id=user.company_id,
            account_type=user.account_type,
            roles=user.roles,
        )
        refresh_token = create_refresh_token(user_id=user.id)

        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.access_token_expire_minutes * 60,
        )

    async def _reload_with_tokens(self, user_id: uuid.UUID) -> tuple[User, TokenPair]:
        """Re-fetches the user with roles eager-loaded, then issues tokens off the fresh row."""
        user = await self._users.get_by_id(user_id)
        assert user is not None  # just created/authenticated in this same transaction
        return user, self._issue_tokens(user)
