# 04 — Roles and permissions

This document answers one question: **who can do what in Talign, and what stops them from doing more?** It starts with the five roles in plain language, then lists what each can do, then explains the rules that apply on top of roles (company isolation, ownership, what candidates can never see), and ends with an endpoint-by-endpoint table that is generated from the code and checked by a test.

---

## 1. The five roles

A role says what a user is allowed to do. Talign has exactly five, defined once in `backend/app/core/roles.py`:

| Role | Who they are | How an account gets this role |
| --- | --- | --- |
| `admin` | The person who set up the company; manages people and company knowledge, and can do everything a recruiter can | Created automatically when someone registers a company (`POST /auth/register/company`) |
| `recruiter` | Runs hiring: jobs, screening, emails, moving candidates through the pipeline | Added by an admin through the API (`POST /auth/internal-users`) |
| `hiring_manager` | Reviews candidates against jobs and approves leave; sees the pipeline but cannot change it | Added by an admin |
| `employee` | Someone who works at the company; uses the employee portal (company knowledge, leave) | Added by an admin, **or** obtained automatically when a hired candidate's account is converted |
| `candidate` | An external person applying for jobs | Created by self-registration (`POST /auth/register/candidate`) |

Alongside roles there is a coarser idea, the **account type**, which has just two values: `internal` (belongs to a company) and `candidate` (belongs to nobody; a platform-wide identity). It exists because the database itself enforces one rule with it: *an internal account must have a company, and a candidate account must not* (the `ck_users_company_assignment` constraint). Admin, recruiter, hiring manager and employee are all internal. A user is allowed to hold several roles in the schema, but every path that creates an account in this version assigns exactly one.

**What the product does not have:** there is no screen for adding users (the add-user endpoint is used by the demo seed script and through the interactive API docs at `/docs`), and no endpoint to list users, disable an account, change a role or reset a password, and no email invitation flow. An admin creates an account directly and tells the person the initial password. These are known limits, listed in the roadmap document.

---

## 2. What each role can do

A tick means the role can perform the action; a dash means the server refuses it. This table summarises the endpoint table in section 5.

| Capability | Candidate | Employee | Hiring manager | Recruiter | Admin |
| --- | :---: | :---: | :---: | :---: | :---: |
| Browse open jobs (no account needed) | ✓ | ✓ | ✓ | ✓ | ✓ |
| Apply to a job; upload and attach resumes; see own applications and their stage | ✓ | — | — | — | — |
| See the analysis (score, strengths, concerns) of a candidate | — | — | ✓ | ✓ | ✓ |
| View jobs, the pipeline, candidate detail, email history, hire-workflow status | — | — | ✓ | ✓ | ✓ |
| Create, edit, open/close/archive, delete (drafts only) jobs | — | — | — | ✓ | ✓ |
| Move a candidate between stages, reject, hire; re-run an analysis | — | — | — | ✓ | ✓ |
| Draft, regenerate, edit and mark-as-sent emails | — | — | — | ✓ | ✓ |
| View the dashboard and daily brief | — | — | ✓ | ✓ | ✓ |
| Read company knowledge documents | — | ✓ | ✓ | ✓ | ✓ |
| Upload, delete and re-index knowledge documents | — | — | — | — | ✓ |
| Ask Compass (what it can answer depends on role, see below) | ✓ | ✓ | ✓ | ✓ | ✓ |
| Request leave, see own requests and balance, cancel own pending request | — | ✓ | — | — | — |
| See the leave approval queue; approve or reject requests | — | — | ✓ | — | ✓ |
| Add a user to the company | — | — | — | — | ✓ |

Two consequences worth spelling out, because they surprise people:

- **A hiring manager reads but does not write the hiring pipeline.** They can see candidates, analyses and emails, but cannot move a candidate, draft an email or create a job. Their write power is leave approval.
- **Admins and hiring managers cannot request leave themselves.** Leave requests belong to the `employee` role, so an admin asking for their own balance is refused (403). Approvers approve other people's leave; they do not have a balance of their own in this MVP.
- **Only a *hired* employee can actually use leave.** The leave screens need an employee *record* (job title, hire date), and only the hire workflow creates one. An account that an admin creates directly with the `employee` role has the role but no record, so it can sign in and read company knowledge, but a leave request or balance lookup answers 404 ("No employee record found for this account."). This was confirmed by running the real backend against a real database while writing this document. It is a genuine gap in the MVP: the add-user endpoint accepts the `employee` role, but only the hire path produces a fully working employee.

### What Compass will answer, by role

Compass is available to everyone signed in, but the *capability* it can use is limited by role and, for staff, by whether a candidate is open. The registry refuses a capability a role does not hold, so rephrasing the question cannot get around it.

| Role | Capability | What it does |
| --- | --- | --- |
| Candidate | `application_status` | Tells the candidate the current stage of one of their own applications. Nothing else; never company documents, never analysis. |
| Employee | `knowledge_query` | Answers company-policy questions from the company's documents, with citations. |
| Admin / recruiter / hiring manager, with a candidate open | `explain_analysis` | Answers questions about that candidate's *stored* analysis. It introduces no new judgement and no new score. |
| Admin / recruiter / hiring manager, no candidate open | `knowledge_query` | Company-policy questions, as for employees. |

---

## 3. Rules that apply on top of roles

**Company isolation.** Every internal user belongs to exactly one company, and every query that returns company data filters by the caller's company (the repositories expose `..._for_company` lookups; `company_id` is copied onto applications, emails, knowledge chunks, leave requests and workflow runs precisely so the filter is direct and cheap). The company always comes from the signed-in user's account, never from anything the client sends. A record from another company is not "forbidden": it is reported as **not found** (404), so the response does not even confirm it exists. Knowledge retrieval is filtered by company *before* similarity ranking, so one company's documents cannot appear in another's answers. The demo seed includes two companies with deliberately different leave policies (20 days against 25) to make this visible, and `tools/sandbox_e2e/verify_isolation.py` asserts it against a running stack.

**Ownership for candidates.** A candidate reaches only their own data. The routes are `/applications/mine…` and `/resumes/mine…`, and a resume that belongs to someone else answers 404 rather than 403.

**What a candidate can never receive.** No route that a candidate's role can pass returns the analysis. The candidate's application-status route returns only a bare progress state (`not_started`, `parsing`, `analyzing`, `complete`, `failed`). This is a structural property, verified by `test_candidate_analysis_exposure.py`, not a field filtered out of a response.

**Public data is separate from internal data.** The public job board (`/public/jobs`) has no authentication at all and serves a dedicated schema that omits internal fields (no company id, creator, status or applicant statistics) and adds the employer's name. It only ever returns jobs whose status is `open`.

**Within a company, access is by role, not by ownership.** Any recruiter can see and change any of their company's jobs and applications; any hiring manager can see the whole company's pipeline; any admin or hiring manager can approve any leave request. There is no per-job assignment and no manager hierarchy. That was a deliberate MVP simplification.

**Business rules are enforced twice.** Where a rule matters, it is checked in the service layer (to give a clear error) and again by a database constraint (so no bug can bypass it). See the data model document for the list.

---

## 4. Where the rules live in the code

| Rule | Location |
| --- | --- |
| The list of roles, and the account-type mapping | `backend/app/core/roles.py` |
| Which role may call which endpoint | A `Depends(require_roles(...))` in each route's signature, in `backend/app/api/v1/*.py`; shared groups are module constants such as `_PIPELINE_READ_ROLES` |
| Reading the signed-in user and rejecting disabled accounts | `backend/app/api/deps.py` |
| Which role may use which Compass capability | `backend/app/compass/capabilities.py` |
| Company scoping | `*_for_company` methods in `backend/app/repositories/` and the services that call them |
| What the frontend shows each role | `frontend/src/components/nav-bar.tsx`, `frontend/src/lib/roles.ts`, `frontend/src/components/compass-panel/compass-scope.ts` |

The frontend's role checks decide only what to *display*. They are a courtesy to the user, not a defence: the server checks every request regardless.

---

## 5. Endpoint-by-endpoint access (generated)

The table below is **generated from the source code** by `backend/scripts/route_access.py` and verified against it by `backend/tests/test_docs_match_code.py`. If you change who may call an endpoint, regenerate it with `python scripts/route_access.py --markdown` and paste the result between the markers. Do not edit it by hand: the test will fail if it no longer matches the code. "Any signed-in user" means a valid session is required but no particular role; "public" means no sign-in is needed (the refresh and logout routes read the refresh cookie instead).

<!-- BEGIN GENERATED: endpoint-access-table -->
| Method | Path | Who may call it |
| --- | --- | --- |
| GET | `/api/v1/health` | public |
| POST | `/api/v1/auth/register/company` | public |
| POST | `/api/v1/auth/register/candidate` | public |
| POST | `/api/v1/auth/login` | public |
| POST | `/api/v1/auth/refresh` | public |
| POST | `/api/v1/auth/logout` | public |
| GET | `/api/v1/auth/me` | any signed-in user |
| POST | `/api/v1/auth/internal-users` | `admin` |
| POST | `/api/v1/jobs` | `admin`, `recruiter` |
| GET | `/api/v1/jobs` | `admin`, `recruiter`, `hiring_manager` |
| GET | `/api/v1/jobs/{job_id}` | `admin`, `recruiter`, `hiring_manager` |
| PATCH | `/api/v1/jobs/{job_id}` | `admin`, `recruiter` |
| POST | `/api/v1/jobs/{job_id}/transition` | `admin`, `recruiter` |
| DELETE | `/api/v1/jobs/{job_id}` | `admin`, `recruiter` |
| GET | `/api/v1/public/jobs` | public |
| GET | `/api/v1/public/jobs/{job_id}` | public |
| POST | `/api/v1/applications` | `candidate` |
| GET | `/api/v1/applications/mine` | `candidate` |
| GET | `/api/v1/applications/mine/{application_id}` | `candidate` |
| PUT | `/api/v1/applications/mine/{application_id}/resume` | `candidate` |
| GET | `/api/v1/applications/mine/{application_id}/analysis-status` | `candidate` |
| GET | `/api/v1/applications` | `admin`, `recruiter`, `hiring_manager` |
| GET | `/api/v1/applications/{application_id}` | `admin`, `recruiter`, `hiring_manager` |
| POST | `/api/v1/applications/{application_id}/transition` | `admin`, `recruiter` |
| GET | `/api/v1/applications/{application_id}/hire-workflow` | `admin`, `recruiter`, `hiring_manager` |
| GET | `/api/v1/applications/{application_id}/analysis` | `admin`, `recruiter`, `hiring_manager` |
| GET | `/api/v1/applications/{application_id}/analysis/history` | `admin`, `recruiter`, `hiring_manager` |
| GET | `/api/v1/applications/{application_id}/analysis-status` | `admin`, `recruiter`, `hiring_manager` |
| POST | `/api/v1/applications/{application_id}/reanalyze` | `admin`, `recruiter` |
| POST | `/api/v1/applications/{application_id}/emails/draft` | `admin`, `recruiter` |
| POST | `/api/v1/applications/{application_id}/emails/{email_id}/regenerate` | `admin`, `recruiter` |
| PATCH | `/api/v1/applications/{application_id}/emails/{email_id}` | `admin`, `recruiter` |
| POST | `/api/v1/applications/{application_id}/emails/{email_id}/send` | `admin`, `recruiter` |
| GET | `/api/v1/applications/{application_id}/emails` | `admin`, `recruiter`, `hiring_manager` |
| POST | `/api/v1/resumes` | `candidate` |
| GET | `/api/v1/resumes/mine` | `candidate` |
| GET | `/api/v1/resumes/mine/{resume_id}` | `candidate` |
| POST | `/api/v1/compass/ask` | any signed-in user |
| POST | `/api/v1/knowledge/documents` | `admin` |
| GET | `/api/v1/knowledge/documents` | `admin`, `recruiter`, `hiring_manager`, `employee` |
| GET | `/api/v1/knowledge/documents/{document_id}` | `admin`, `recruiter`, `hiring_manager`, `employee` |
| DELETE | `/api/v1/knowledge/documents/{document_id}` | `admin` |
| POST | `/api/v1/knowledge/documents/{document_id}/reindex` | `admin` |
| GET | `/api/v1/dashboard` | `admin`, `recruiter`, `hiring_manager` |
| POST | `/api/v1/leave-requests` | `employee` |
| GET | `/api/v1/leave-requests/mine` | `employee` |
| GET | `/api/v1/leave-requests/mine/balance` | `employee` |
| POST | `/api/v1/leave-requests/{leave_request_id}/cancel` | `employee` |
| GET | `/api/v1/leave-requests` | `admin`, `hiring_manager` |
| POST | `/api/v1/leave-requests/{leave_request_id}/approve` | `admin`, `hiring_manager` |
| POST | `/api/v1/leave-requests/{leave_request_id}/reject` | `admin`, `hiring_manager` |
<!-- END GENERATED: endpoint-access-table -->


For the request and response shape of each endpoint, see the API reference (05).
