# 01 — Slice 1: Authentication & Identity

## Purpose

Company registration, candidate registration, login, token refresh,
logout, and RBAC — the identity foundation every later slice depends on.
Ships database, backend, API, and frontend together, per the vertical-
slice development strategy.

## What was built

```
backend/app/
├── models/
│   ├── company.py       Company
│   ├── role.py           Role (lookup table), UserRole (join table)
│   └── user.py            User — see "Company assignment rule" below
├── core/
│   ├── enums.py           UserStatus (account lifecycle)
│   ├── roles.py            + AccountType, account_type_for_role()
│   ├── security.py        password hashing, JWT encode/decode
│   └── exceptions.py      domain exception hierarchy
├── repositories/
│   ├── company_repository.py
│   ├── role_repository.py
│   └── user_repository.py
├── services/
│   └── auth_service.py    ALL business logic — see below
├── schemas/
│   ├── user.py             UserRead
│   └── auth.py             Register*/Login/Token* request+response shapes
├── api/
│   ├── deps.py              get_current_user, require_roles
│   └── v1/auth.py           register/company, register/candidate, login,
│                             refresh, logout, me, internal-users
└── alembic/versions/
    └── ..._slice1_authentication_identity.py

frontend/src/
├── features/auth/
│   ├── types.ts             mirrors backend schemas + Zod validation
│   ├── api.ts                 thin apiFetch wrappers
│   ├── hooks/use-auth.tsx    AuthProvider — in-memory access token,
│   │                          silent refresh on mount
│   └── components/            LoginForm, RegisterCompanyForm, RegisterCandidateForm
├── app/(auth)/login, register/company, register/candidate
├── app/(protected)/dashboard    proves the loop end-to-end; real
│                                  Dashboard module ships later
└── middleware.ts                UX-only redirect (see below — NOT the
                                    security boundary)
```

## Key architectural decisions

### 1. Company-assignment rule — enforced at two layers, as instructed

**DB layer** — `ck_users_company_assignment` CHECK constraint on `users`:

```sql
CHECK (
  (account_type = 'candidate' AND company_id IS NULL)
  OR (account_type = 'internal' AND company_id IS NOT NULL)
)
```

**Service layer** — `AuthService._assert_company_assignment_valid`, called
from `_register_user`, the single choke point every registration path
(`register_company`, `register_candidate`, `create_internal_user`) routes
through. A violation raises `InvalidCompanyAssignmentError` (422) before
any insert is attempted — the DB constraint is the last line of defense,
not the primary one, so violations surface as clean domain errors rather
than raw `IntegrityError`s.

Verified directly in `tests/test_auth_service_rules.py` (four cases: all
combinations of account_type × company_id presence) with zero database
required — the validator is a pure function, which is exactly why it was
factored out as a `staticmethod` rather than inlined.

### 2. `account_type` vs `Role` — two different questions

`Role`/`UserRole` (existing since Slice 0's `core/roles.py`) answers "what
can this user do" — fine-grained RBAC, a user can hold several. The new
`AccountType` enum (`internal` | `candidate`) answers a coarser question:
"does this identity belong to a company, or to the platform itself." It's
what the CHECK constraint keys off, specifically so that constraint
doesn't need to join against `user_roles` to enforce anything. One
function, `account_type_for_role()`, is the single place mapping a Role
to its AccountType — if a V2 role is ever added, that's the only line
that needs to know whether it's internal or platform-wide.

### 3. Domain exceptions, translated at one boundary

`app/core/exceptions.py` defines a `TalignError` hierarchy
(`ConflictError`, `AuthenticationError`, `DomainValidationError`, ...).
Services raise these and only these — never `fastapi.HTTPException`. One
handler in `main.py` (`@app.exception_handler(TalignError)`) is the sole
place that knows domain errors map to HTTP status codes. This keeps
`AuthService` importable and testable with zero FastAPI in the loop,
which is exactly what `tests/test_auth_service_rules.py` exploits.

### 4. Token design: split access/refresh, only refresh is a cookie

- **Access token**: short-lived (30 min default), returned in the JSON
  response body, sent as an `Authorization: Bearer` header. Held in a
  React `ref` on the frontend (not `localStorage`, not `sessionStorage`)
  — gone on page reload by design.
- **Refresh token**: long-lived (14 days default), set as an `httpOnly`,
  `SameSite=Lax` cookie scoped to `path=/api/v1/auth` only. Never
  readable by frontend JS. Rotated on every use (`/auth/refresh` issues
  a new refresh token, not just a new access token).

This is the standard mitigation for XSS: if an attacker's script runs on
the page, it can see `document.cookie` for non-httpOnly cookies and any
JS variables, but the refresh token is in neither of those — worst case
an XSS payload steals a 30-minute access token, not a 14-day one.

### 5. The `talign_session` cookie is NOT a security boundary

Real snag surfaced during implementation: the refresh cookie's
`path=/api/v1/auth` scoping (correct — it should only ever be sent to
the refresh endpoint) means Next.js edge middleware, which runs against
requests to the frontend's own routes (`/dashboard`, port 3000), never
sees it. Widening the cookie's path to `/` just to make it visible to
middleware would weaken it for zero real benefit.

Instead, a second cookie — `talign_session`, non-httpOnly, `path=/`,
holding only `"1"` — is set alongside the refresh cookie. Middleware
checks for its presence to redirect unauthenticated visitors away from
`/dashboard` early, and authenticated visitors away from `/login`. If
someone forges this cookie, the worst outcome is landing on a page that
immediately fails its real check (`get_current_user`'s bearer-token
validation) — it grants zero actual access. This distinction is
documented directly in the cookie-setting code, not just here, since
it's the kind of thing that looks like a security control if you don't
read the comment.

### 6. Candidate self-registration vs. admin-created internal users

Two different code paths, intentionally:

- `register_company` / `register_candidate` — public, unauthenticated,
  self-service. First hit creates the Company (for the admin path) or
  just the User (candidate path).
- `create_internal_user` — requires `Depends(require_roles(Role.ADMIN))`.
  `acting_company_id` is read from the **authenticated caller's token**,
  never from the request body, so an admin literally cannot create a
  user in a company they don't belong to — there's no field to tamper
  with. This is the simplified stand-in for the Product Book's "HR
  Director invites Recruiter" flow — see deferred scope below.

### 7. What's deferred, and why

- **Email-based invitations** (token link, "Recruiter receives email,
  creates account" per the Product Book's Authentication module) —
  `create_internal_user` requires the admin to set a password directly
  instead. Real invites need outbound email, which depends on
  infrastructure (Communication Agent or at minimum a mail-sending
  service) that doesn't exist yet. Building a bespoke invite-email path
  now would be throwaway work once the Communication Agent ships.
- **Password reset** — already marked Future in the Product Book's own
  domain model; unchanged here.
- **"Logout everywhere" / refresh token revocation list** — the current
  refresh flow trusts any unexpired, correctly-signed refresh token.
  Revoking a specific session (e.g., "someone stole my laptop") needs a
  server-side token registry (jti blacklist or allowlist), deferred
  until there's a real feature consuming it — premature to build now
  per the "avoid unnecessary abstractions" principle.
- **Server-side (edge) authorization** — middleware.ts is UX-only (see
  #5). Real per-route server-side authorization, if needed later (e.g.
  for server components that must not even render for the wrong role),
  would call `/auth/me` server-side rather than trust any cookie.

## Verifying Slice 1

```bash
cp .env.example .env
docker compose up --build
```

Manual flow:
1. `POST http://localhost:8000/api/v1/auth/register/company` with
   `{company_name, admin_first_name, admin_last_name, email, password}`
   → 201, `TokenResponse` with `user.account_type == "internal"` and
   `user.roles == ["admin"]`.
2. `POST .../auth/register/candidate` with
   `{first_name, last_name, email, password}` → 201, `user.company_id`
   is `null`, `user.account_type == "candidate"`.
3. `GET .../auth/me` with `Authorization: Bearer <access_token>` → the
   same user.
4. `POST .../auth/refresh` (browser sends the httpOnly cookie
   automatically) → new access token.
5. Frontend: visit `http://localhost:3000`, register a company, land on
   `/dashboard`, reload the page — session persists via silent refresh.

Automated:
```bash
cd backend && pytest         # 10 tests: security round-trips + the
                               # four company-assignment rule cases
cd frontend && npx tsc --noEmit && npx next build
```

## Next: Slice 2 — Jobs (Recruiter-facing CRUD)

First deterministic, no-AI domain module — proves out the
service/repository layering on a simpler entity before Slice 3
(Candidate Application Flow) exercises the Candidate account model
built here, and Slice 4 introduces the first real Agent.
