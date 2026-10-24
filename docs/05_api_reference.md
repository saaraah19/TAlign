# 05 — API reference

> **This file is generated.** It is produced from the application's OpenAPI schema by
> `backend/scripts/generate_api_reference.py` and checked by
> `backend/tests/test_docs_match_code.py`. Do not edit it by hand: change the code, then run
> `python scripts/generate_api_reference.py` from `backend/`.

Talign's API is a JSON REST API. When the backend is running you can also explore and call it
interactively at `http://localhost:8000/docs` (Swagger UI) or read the raw schema at
`http://localhost:8000/openapi.json`. This page is the same information in a form you can read
without running anything, plus a "who may call this" column that the schema itself cannot express.

## Conventions

**Base URL.** Every path below is relative to the backend's address, for example
`http://localhost:8000`. All business endpoints live under `/api/v1`.

**Authentication.** Sign in with `POST /api/v1/auth/login`; the response contains an
`access_token`. Send it on every protected request as `Authorization: Bearer <token>`. The access
token is short-lived (30 minutes by default). Sign-in also sets an `httpOnly` refresh cookie
(path `/api/v1/auth`) that `POST /api/v1/auth/refresh` exchanges for a new access token.

**Access.** The "Access" line of each endpoint says who may call it: a list of roles, "any
signed-in user" (a valid token and no particular role), or "public" (no token). A caller without
the required role receives `403`; a missing or invalid token receives `401`. Records belonging to
another company are reported as `404`, never `403`.

**Errors.** Domain errors return `{"detail": "<human-readable message>"}` with the status code
that fits the error: `401` authentication, `403` permission, `404` not found (including "not
yours"), `409` conflict (duplicate, already done, overlapping), `422` invalid input or an illegal
state change, `429` too many failed logins (with a `Retry-After` header), `502` the AI provider
failed or answered unusably, `500` an unexpected error. Malformed request bodies are rejected by
FastAPI with `422` and a `detail` list describing each problem.

**Lists.** List endpoints that page results accept `page` (from 1) and `page_size`, and return the
page's `items` together with `total`, `page` and `page_size`.

**IDs and dates.** Identifiers are UUIDs. Timestamps are ISO 8601 in UTC. Dates (leave requests,
hire dates) are `YYYY-MM-DD`.

**Counts.** 51 operations across 11 areas, using 71 schemas.

## Endpoints

## Health

### `GET /api/v1/health`

Liveness check. Reports whether the API is up and the database reachable (`status`, `database`).

**Access:** public

**Returns:** `200` object

## Authentication

### `POST /api/v1/auth/register/company`

Creates a company and its first user, an `admin`, then signs them in (access token in the body, refresh cookie set). `409` if the email is already registered.

**Access:** public

**Request body:** `RegisterCompanyRequest` (JSON)

**Returns:** `201` `TokenResponse`

### `POST /api/v1/auth/register/candidate`

Creates a candidate account (no company; it can apply to jobs at any company) and signs it in. `409` if the email is already registered.

**Access:** public

**Request body:** `RegisterCandidateRequest` (JSON)

**Returns:** `201` `TokenResponse`

### `POST /api/v1/auth/login`

Checks email and password and signs the user in: returns an access token and sets the refresh cookie. `401` for wrong credentials or a disabled account. After 5 failed attempts within 15 minutes for the same client address and email, further attempts are refused with `429` and a `Retry-After` header, even with the correct password.

**Access:** public

**Request body:** `LoginRequest` (JSON)

**Returns:** `200` `TokenResponse`

### `POST /api/v1/auth/refresh`

Exchanges the refresh cookie for a new access token. `401` if the cookie is missing, invalid or expired, or the account is no longer active.

**Access:** public

| Parameter | In | Type | Required | Notes |
| --- | --- | --- | :---: | --- |
| `talign_refresh_token` | cookie | string (or null) |  |  |

**Returns:** `200` `AccessTokenResponse`

### `POST /api/v1/auth/logout`

Clears the refresh and session cookies. Always succeeds, even when already signed out.

**Access:** public

**Returns:** `204` Successful Response

### `GET /api/v1/auth/me`

Returns the signed-in user: id, company, account type, status and roles.

**Access:** any signed-in user

**Returns:** `200` `UserRead`

### `POST /api/v1/auth/internal-users`

An admin adds a user to their own company with an initial password. `role` must be `admin`, `recruiter`, `hiring_manager` or `employee` (`422` for an unknown role or `candidate`). `409` if the email is taken. Note: a user created with the `employee` role this way has no employee record, so leave endpoints answer `404` for it; only the hire workflow produces a fully working employee.

**Access:** `admin`

**Request body:** `CreateInternalUserRequest` (JSON)

**Returns:** `201` `UserRead`

## Jobs (staff)

### `POST /api/v1/jobs`

Creates a job in the caller's company. It starts as a `draft`. The three scoring criteria (`required_skills`, `preferred_skills`, `min_years_experience`) are what candidates are scored against.

**Access:** `admin`, `recruiter`

**Request body:** `JobCreateRequest` (JSON)

**Returns:** `201` `JobRead`

### `GET /api/v1/jobs`

Lists the company's jobs, newest first, each with applicant statistics. Optional `status` filter; paged.

**Access:** `admin`, `recruiter`, `hiring_manager`

| Parameter | In | Type | Required | Notes |
| --- | --- | --- | :---: | --- |
| `status` | query | `JobStatus` (or null) |  |  |
| `page` | query | integer |  | min 1; default `1` |
| `page_size` | query | integer |  | min 1; max 100; default `20` |

**Returns:** `200` `JobListResponse`

### `GET /api/v1/jobs/{job_id}`

One job of the caller's company. `404` if it does not exist or belongs to another company.

**Access:** `admin`, `recruiter`, `hiring_manager`

| Parameter | In | Type | Required | Notes |
| --- | --- | --- | :---: | --- |
| `job_id` | path | string (uuid) | yes |  |

**Returns:** `200` `JobRead`

### `PATCH /api/v1/jobs/{job_id}`

Partially updates a job's editable fields (title, description, type, location, salary, skills and experience criteria). It cannot change the status; use the transition endpoint. The frontend has no screen for this yet.

**Access:** `admin`, `recruiter`

| Parameter | In | Type | Required | Notes |
| --- | --- | --- | :---: | --- |
| `job_id` | path | string (uuid) | yes |  |

**Request body:** `JobUpdateRequest` (JSON)

**Returns:** `200` `JobRead`

### `DELETE /api/v1/jobs/{job_id}`

Deletes a job. Only a `draft` can be deleted (`422` otherwise); a published job is closed and archived instead.

**Access:** `admin`, `recruiter`

| Parameter | In | Type | Required | Notes |
| --- | --- | --- | :---: | --- |
| `job_id` | path | string (uuid) | yes |  |

**Returns:** `204` Successful Response

### `POST /api/v1/jobs/{job_id}/transition`

Moves a job one step along `draft`, `open`, `closed`, `archived` (no skipping, no going back). `422` for an illegal move.

**Access:** `admin`, `recruiter`

| Parameter | In | Type | Required | Notes |
| --- | --- | --- | :---: | --- |
| `job_id` | path | string (uuid) | yes |  |

**Request body:** `JobStatusTransitionRequest` (JSON)

**Returns:** `200` `JobRead`

## Public

### `GET /api/v1/public/jobs`

The public job board: every `open` job across all companies, newest first, with the employer's name. No sign-in. Paged.

**Access:** public

| Parameter | In | Type | Required | Notes |
| --- | --- | --- | :---: | --- |
| `page` | query | integer |  | min 1; default `1` |
| `page_size` | query | integer |  | min 1; max 100; default `20` |

**Returns:** `200` `PublicJobListResponse`

### `GET /api/v1/public/jobs/{job_id}`

One public job. `404` unless the job is `open`. Internal fields (creator, status, applicant statistics, company id) are never included.

**Access:** public

| Parameter | In | Type | Required | Notes |
| --- | --- | --- | :---: | --- |
| `job_id` | path | string (uuid) | yes |  |

**Returns:** `200` `PublicJobRead`

## Applications

### `POST /api/v1/applications`

A candidate applies to a job. The job must be `open` (`422` otherwise) and the candidate can apply to a given job only once (`409`). Returns the new application; attach a resume afterwards.

**Access:** `candidate`

**Request body:** `ApplicationCreateRequest` (JSON)

**Returns:** `201` `ApplicationWithJob`

### `GET /api/v1/applications`

Staff view of the company's pipeline: applications with candidate, job and alignment score. Optional `job_id` and `status` filters; paged (up to 100 per page).

**Access:** `admin`, `recruiter`, `hiring_manager`

| Parameter | In | Type | Required | Notes |
| --- | --- | --- | :---: | --- |
| `job_id` | query | string (uuid) (or null) |  |  |
| `status` | query | `ApplicationStatus` (or null) |  |  |
| `page` | query | integer |  | min 1; default `1` |
| `page_size` | query | integer |  | min 1; max 100; default `20` |

**Returns:** `200` `PipelineListResponse`

### `GET /api/v1/applications/mine`

The signed-in candidate's own applications, with job and employer. Paged.

**Access:** `candidate`

| Parameter | In | Type | Required | Notes |
| --- | --- | --- | :---: | --- |
| `page` | query | integer |  | min 1; default `1` |
| `page_size` | query | integer |  | min 1; max 100; default `20` |

**Returns:** `200` `ApplicationListResponse`

### `GET /api/v1/applications/mine/{application_id}`

One of the candidate's own applications. `404` for anyone else's.

**Access:** `candidate`

| Parameter | In | Type | Required | Notes |
| --- | --- | --- | :---: | --- |
| `application_id` | path | string (uuid) | yes |  |

**Returns:** `200` `ApplicationWithJob`

### `PUT /api/v1/applications/mine/{application_id}/resume`

Attaches (or replaces) one of the candidate's own resumes on their application and starts the automated analysis in the background. `404` if the resume is not theirs.

**Access:** `candidate`

| Parameter | In | Type | Required | Notes |
| --- | --- | --- | :---: | --- |
| `application_id` | path | string (uuid) | yes |  |

**Request body:** `AttachResumeRequest` (JSON)

**Returns:** `200` `ApplicationWithJob`

### `GET /api/v1/applications/mine/{application_id}/analysis-status`

The progress of the automated review for the candidate's own application: `not_started`, `parsing`, `analyzing`, `complete` or `failed`. Progress only, never analysis content.

**Access:** `candidate`

| Parameter | In | Type | Required | Notes |
| --- | --- | --- | :---: | --- |
| `application_id` | path | string (uuid) | yes |  |

**Returns:** `200` `AnalysisProgressStatusRead`

### `GET /api/v1/applications/{application_id}`

Staff detail of one application, including the candidate's basic information. `404` for another company's application.

**Access:** `admin`, `recruiter`, `hiring_manager`

| Parameter | In | Type | Required | Notes |
| --- | --- | --- | :---: | --- |
| `application_id` | path | string (uuid) | yes |  |

**Returns:** `200` `ApplicationWithCandidate`

### `POST /api/v1/applications/{application_id}/transition`

Moves an application one step forward (`applied`, `screening`, `interview`, `offer`, `hired`) or rejects it from any stage before the end. `hired` and `rejected` are final. Moving to `hired` starts the hire workflow in the background. `422` for an illegal move.

**Access:** `admin`, `recruiter`

| Parameter | In | Type | Required | Notes |
| --- | --- | --- | :---: | --- |
| `application_id` | path | string (uuid) | yes |  |

**Request body:** `ApplicationStatusTransitionRequest` (JSON)

**Returns:** `200` `ApplicationWithCandidate`

### `GET /api/v1/applications/{application_id}/hire-workflow`

The outcome of the hire workflow for a hired application: the workflow run (success, failed or skipped, with the failing step), the employee record and the onboarding tasks. Each is `null` or empty until it exists, so a client can poll.

**Access:** `admin`, `recruiter`, `hiring_manager`

| Parameter | In | Type | Required | Notes |
| --- | --- | --- | :---: | --- |
| `application_id` | path | string (uuid) | yes |  |

**Returns:** `200` `HireWorkflowStatusRead`

### `GET /api/v1/applications/{application_id}/analysis`

The latest completed resume analysis: overall score, the three dimension percentages, per-skill results with evidence, strengths, concerns, explanation and provenance. `404` if none is completed yet.

**Access:** `admin`, `recruiter`, `hiring_manager`

| Parameter | In | Type | Required | Notes |
| --- | --- | --- | :---: | --- |
| `application_id` | path | string (uuid) | yes |  |

**Returns:** `200` `ResumeAnalysisRead`

### `GET /api/v1/applications/{application_id}/analysis/history`

Every analysis ever run for the application (including failed ones), newest first. Analyses are never overwritten.

**Access:** `admin`, `recruiter`, `hiring_manager`

| Parameter | In | Type | Required | Notes |
| --- | --- | --- | :---: | --- |
| `application_id` | path | string (uuid) | yes |  |

**Returns:** `200` `ResumeAnalysisHistoryResponse`

### `GET /api/v1/applications/{application_id}/analysis-status`

The same progress states as the candidate's version, for staff.

**Access:** `admin`, `recruiter`, `hiring_manager`

| Parameter | In | Type | Required | Notes |
| --- | --- | --- | :---: | --- |
| `application_id` | path | string (uuid) | yes |  |

**Returns:** `200` `AnalysisProgressStatusRead`

### `POST /api/v1/applications/{application_id}/reanalyze`

Starts a fresh analysis of the attached resume in the background and returns `202` with the current progress. A new analysis row is added; nothing is overwritten.

**Access:** `admin`, `recruiter`

| Parameter | In | Type | Required | Notes |
| --- | --- | --- | :---: | --- |
| `application_id` | path | string (uuid) | yes |  |

**Returns:** `202` `AnalysisProgressStatusRead`

## Emails (on an application)

### `POST /api/v1/applications/{application_id}/emails/draft`

Drafts an email of the requested type with the AI. Idempotent: if a draft of that type already exists it is returned and no new model call is made. `409` if the application is already `hired` or `rejected`, so draft a rejection before rejecting. Nothing is sent.

**Access:** `admin`, `recruiter`

| Parameter | In | Type | Required | Notes |
| --- | --- | --- | :---: | --- |
| `application_id` | path | string (uuid) | yes |  |

**Request body:** `DraftEmailRequest` (JSON)

**Returns:** `200` `EmailRead`

### `POST /api/v1/applications/{application_id}/emails/{email_id}/regenerate`

Replaces a draft's subject and body with a fresh AI draft. `409` if the email was already sent. Known issue: it does not yet support `onboarding_welcome` drafts (see docs/11).

**Access:** `admin`, `recruiter`

| Parameter | In | Type | Required | Notes |
| --- | --- | --- | :---: | --- |
| `application_id` | path | string (uuid) | yes |  |
| `email_id` | path | string (uuid) | yes |  |

**Returns:** `200` `EmailRead`

### `PATCH /api/v1/applications/{application_id}/emails/{email_id}`

Manually edits a draft's subject and body (no AI call). `409` if the email was already sent.

**Access:** `admin`, `recruiter`

| Parameter | In | Type | Required | Notes |
| --- | --- | --- | :---: | --- |
| `application_id` | path | string (uuid) | yes |  |
| `email_id` | path | string (uuid) | yes |  |

**Request body:** `UpdateEmailRequest` (JSON)

**Returns:** `200` `EmailRead`

### `POST /api/v1/applications/{application_id}/emails/{email_id}/send`

Records that the recruiter has sent the draft. Talign sends no email itself. A sent email is permanently read-only (`409` if already sent).

**Access:** `admin`, `recruiter`

| Parameter | In | Type | Required | Notes |
| --- | --- | --- | :---: | --- |
| `application_id` | path | string (uuid) | yes |  |
| `email_id` | path | string (uuid) | yes |  |

**Returns:** `200` `EmailRead`

### `GET /api/v1/applications/{application_id}/emails`

All drafted and sent emails for the application.

**Access:** `admin`, `recruiter`, `hiring_manager`

| Parameter | In | Type | Required | Notes |
| --- | --- | --- | :---: | --- |
| `application_id` | path | string (uuid) | yes |  |

**Returns:** `200` `EmailListResponse`

## Resumes (candidate)

### `POST /api/v1/resumes`

A candidate uploads a resume as a multipart `file` (PDF, DOCX or plain text, up to 5 MB; `422` for another file type or a file that is too large). Text is extracted immediately without AI; the result's status is `text_ready` or `parse_failed` (for example a scanned PDF).

**Access:** `candidate`

**Request body:** `Body_upload_resume_api_v1_resumes_post` (JSON)

**Returns:** `201` `ResumeRead`

### `GET /api/v1/resumes/mine`

The signed-in candidate's own resumes.

**Access:** `candidate`

**Returns:** `200` list of `ResumeRead`

### `GET /api/v1/resumes/mine/{resume_id}`

One of the candidate's own resumes. `404` if it belongs to someone else.

**Access:** `candidate`

| Parameter | In | Type | Required | Notes |
| --- | --- | --- | :---: | --- |
| `resume_id` | path | string (uuid) | yes |  |

**Returns:** `200` `ResumeRead`

## Compass

### `POST /api/v1/compass/ask`

Asks Compass a question. What it can answer depends on the caller's role and on `application_id`: candidates get the stage of their own application; employees get company-policy answers; staff get an explanation of the given application's stored analysis, or a policy answer when no application is given. The answer names the `capability_used`; policy answers include citations and a confidence level.

**Access:** any signed-in user

**Request body:** `CompassAskRequest` (JSON)

**Returns:** `200` `CompassAskResponse`

## Knowledge documents

### `POST /api/v1/knowledge/documents`

An admin uploads a company document as multipart `file`, `title` and `category` (PDF, DOCX or TXT, up to 20 MB). Text extraction and chunking happen in the request; embedding continues in the background, so the returned status is not yet `ready`.

**Access:** `admin`

**Request body:** `Body_upload_knowledge_document_api_v1_knowledge_documents_post` (JSON)

**Returns:** `201` `KnowledgeDocumentRead`

### `GET /api/v1/knowledge/documents`

The company's knowledge documents with their processing status. Optional `category` filter; paged.

**Access:** `admin`, `recruiter`, `hiring_manager`, `employee`

| Parameter | In | Type | Required | Notes |
| --- | --- | --- | :---: | --- |
| `category` | query | `DocumentCategory` (or null) |  |  |
| `page` | query | integer |  | min 1; default `1` |
| `page_size` | query | integer |  | min 1; max 100; default `20` |

**Returns:** `200` `KnowledgeDocumentListResponse`

### `GET /api/v1/knowledge/documents/{document_id}`

One knowledge document with its status and any processing error.

**Access:** `admin`, `recruiter`, `hiring_manager`, `employee`

| Parameter | In | Type | Required | Notes |
| --- | --- | --- | :---: | --- |
| `document_id` | path | string (uuid) | yes |  |

**Returns:** `200` `KnowledgeDocumentRead`

### `DELETE /api/v1/knowledge/documents/{document_id}`

An admin deletes a document and everything derived from it (its chunks and embeddings).

**Access:** `admin`

| Parameter | In | Type | Required | Notes |
| --- | --- | --- | :---: | --- |
| `document_id` | path | string (uuid) | yes |  |

**Returns:** `204` Successful Response

### `POST /api/v1/knowledge/documents/{document_id}/reindex`

An admin re-runs extraction, chunking and embedding for a document (for example after a failure or a change of embedding model).

**Access:** `admin`

| Parameter | In | Type | Required | Notes |
| --- | --- | --- | :---: | --- |
| `document_id` | path | string (uuid) | yes |  |

**Returns:** `200` `KnowledgeDocumentRead`

## Dashboard

### `GET /api/v1/dashboard`

Everything the recruiter dashboard shows: the cached daily brief (or `null` if it could not be generated), the open-jobs, active-candidates and pending-actions figures, the stage counts for the funnel, and the lists of applications awaiting review, low-applicant jobs, recent analyses, recent hire-workflow runs and pending draft emails (each capped at 10).

**Access:** `admin`, `recruiter`, `hiring_manager`

**Returns:** `200` `DashboardRead`

## Leave requests

### `POST /api/v1/leave-requests`

An employee requests leave (`start_date`, `end_date`, `leave_type`, optional `reason`). `422` if the end is before the start; `409` if it overlaps a pending or approved request of theirs; `404` if the account has no employee record.

**Access:** `employee`

**Request body:** `LeaveRequestCreateRequest` (JSON)

**Returns:** `201` `LeaveRequestRead`

### `GET /api/v1/leave-requests`

The company's leave requests for approval, with the employee's details. Optional `status` filter; paged.

**Access:** `admin`, `hiring_manager`

| Parameter | In | Type | Required | Notes |
| --- | --- | --- | :---: | --- |
| `status` | query | `LeaveRequestStatus` (or null) |  |  |
| `page` | query | integer |  | min 1; default `1` |
| `page_size` | query | integer |  | min 1; max 100; default `20` |

**Returns:** `200` `LeaveRequestPipelineListResponse`

### `GET /api/v1/leave-requests/mine`

The signed-in employee's own leave requests. Paged.

**Access:** `employee`

| Parameter | In | Type | Required | Notes |
| --- | --- | --- | :---: | --- |
| `page` | query | integer |  | min 1; default `1` |
| `page_size` | query | integer |  | min 1; max 100; default `20` |

**Returns:** `200` `LeaveRequestListResponse`

### `GET /api/v1/leave-requests/mine/balance`

The employee's balance for a calendar year (`year`, default the current year): the fixed annual allotment (20 days), days used by approved requests (calendar days, both ends inclusive) and days remaining, which can be negative.

**Access:** `employee`

| Parameter | In | Type | Required | Notes |
| --- | --- | --- | :---: | --- |
| `year` | query | integer (or null) |  |  |

**Returns:** `200` `LeaveBalanceRead`

### `POST /api/v1/leave-requests/{leave_request_id}/cancel`

An employee cancels their own pending request. Final: `422` if it is no longer pending.

**Access:** `employee`

| Parameter | In | Type | Required | Notes |
| --- | --- | --- | :---: | --- |
| `leave_request_id` | path | string (uuid) | yes |  |

**Returns:** `200` `LeaveRequestRead`

### `POST /api/v1/leave-requests/{leave_request_id}/approve`

An admin or hiring manager approves a pending request in their company. Final: `422` if it is no longer pending. Approval is allowed even past the employee's allotment.

**Access:** `admin`, `hiring_manager`

| Parameter | In | Type | Required | Notes |
| --- | --- | --- | :---: | --- |
| `leave_request_id` | path | string (uuid) | yes |  |

**Returns:** `200` `LeaveRequestWithEmployee`

### `POST /api/v1/leave-requests/{leave_request_id}/reject`

An admin or hiring manager rejects a pending request in their company. Final: `422` if it is no longer pending.

**Access:** `admin`, `hiring_manager`

| Parameter | In | Type | Required | Notes |
| --- | --- | --- | :---: | --- |
| `leave_request_id` | path | string (uuid) | yes |  |

**Returns:** `200` `LeaveRequestWithEmployee`

## Schemas

Every request and response shape referenced above. *Required* means the field must be present; a type marked "(or null)" may be sent or returned as `null`.

#### `AccessTokenResponse`

| Field | Type | Required | Notes |
| --- | --- | :---: | --- |
| `access_token` | string | yes |  |
| `token_type` | string |  | default `bearer` |
| `expires_in` | integer | yes |  |

#### `AccountType`

One of: `internal`, `candidate`.

#### `AnalysisProgressStatus`

One of: `not_started`, `parsing`, `analyzing`, `complete`, `failed`.

#### `AnalysisProgressStatusRead`

| Field | Type | Required | Notes |
| --- | --- | :---: | --- |
| `status` | `AnalysisProgressStatus` | yes |  |

#### `ApplicationCandidateSummary`

| Field | Type | Required | Notes |
| --- | --- | :---: | --- |
| `id` | string (uuid) | yes |  |
| `first_name` | string | yes |  |
| `last_name` | string | yes |  |
| `email` | string | yes |  |

#### `ApplicationCreateRequest`

| Field | Type | Required | Notes |
| --- | --- | :---: | --- |
| `job_id` | string (uuid) | yes |  |

#### `ApplicationJobSummary`

| Field | Type | Required | Notes |
| --- | --- | :---: | --- |
| `id` | string (uuid) | yes |  |
| `title` | string | yes |  |
| `company_id` | string (uuid) | yes |  |

#### `ApplicationListResponse`

| Field | Type | Required | Notes |
| --- | --- | :---: | --- |
| `items` | list of `ApplicationWithJob` | yes |  |
| `total` | integer | yes |  |
| `page` | integer | yes |  |
| `page_size` | integer | yes |  |

#### `ApplicationStatus`

One of: `applied`, `screening`, `interview`, `offer`, `hired`, `rejected`.

#### `ApplicationStatusTransitionRequest`

| Field | Type | Required | Notes |
| --- | --- | :---: | --- |
| `target_status` | `ApplicationStatus` | yes |  |

#### `ApplicationWithCandidate`

| Field | Type | Required | Notes |
| --- | --- | :---: | --- |
| `id` | string (uuid) | yes |  |
| `candidate_id` | string (uuid) | yes |  |
| `job_id` | string (uuid) | yes |  |
| `company_id` | string (uuid) | yes |  |
| `status` | `ApplicationStatus` | yes |  |
| `created_at` | string (date-time) | yes |  |
| `updated_at` | string (date-time) | yes |  |
| `candidate` | `ApplicationCandidateSummary` | yes |  |
| `job` | `ApplicationJobSummary` | yes |  |

#### `ApplicationWithJob`

| Field | Type | Required | Notes |
| --- | --- | :---: | --- |
| `id` | string (uuid) | yes |  |
| `candidate_id` | string (uuid) | yes |  |
| `job_id` | string (uuid) | yes |  |
| `company_id` | string (uuid) | yes |  |
| `status` | `ApplicationStatus` | yes |  |
| `created_at` | string (date-time) | yes |  |
| `updated_at` | string (date-time) | yes |  |
| `job` | `ApplicationJobSummary` | yes |  |

#### `ApplicationWithScore`

| Field | Type | Required | Notes |
| --- | --- | :---: | --- |
| `id` | string (uuid) | yes |  |
| `candidate_id` | string (uuid) | yes |  |
| `job_id` | string (uuid) | yes |  |
| `company_id` | string (uuid) | yes |  |
| `status` | `ApplicationStatus` | yes |  |
| `created_at` | string (date-time) | yes |  |
| `updated_at` | string (date-time) | yes |  |
| `candidate` | `ApplicationCandidateSummary` | yes |  |
| `job` | `ApplicationJobSummary` | yes |  |
| `latest_score` | number (or null) |  |  |

#### `AttachResumeRequest`

| Field | Type | Required | Notes |
| --- | --- | :---: | --- |
| `resume_id` | string (uuid) | yes |  |

#### `Body_upload_knowledge_document_api_v1_knowledge_documents_post`

| Field | Type | Required | Notes |
| --- | --- | :---: | --- |
| `file` | string | yes |  |
| `title` | string | yes |  |
| `category` | `DocumentCategory` | yes |  |

#### `Body_upload_resume_api_v1_resumes_post`

| Field | Type | Required | Notes |
| --- | --- | :---: | --- |
| `file` | string | yes |  |

#### `CompassAskRequest`

| Field | Type | Required | Notes |
| --- | --- | :---: | --- |
| `message` | string | yes |  |
| `application_id` | string (uuid) (or null) |  |  |

#### `CompassAskResponse`

| Field | Type | Required | Notes |
| --- | --- | :---: | --- |
| `message` | string | yes |  |
| `capability_used` | string (or null) | yes |  |
| `citations` | list of `KnowledgeCitationRead` (or null) |  |  |
| `confidence` | string (or null) |  |  |

#### `CreateInternalUserRequest`

| Field | Type | Required | Notes |
| --- | --- | :---: | --- |
| `email` | string (email) | yes |  |
| `first_name` | string | yes | min length 1; max length 100 |
| `last_name` | string | yes | min length 1; max length 100 |
| `role` | string | yes |  |
| `password` | string | yes | min length 8; max length 128 |

#### `Currency`

One of: `USD`, `EUR`, `GBP`, `CAD`.

#### `DashboardBriefRead`

| Field | Type | Required | Notes |
| --- | --- | :---: | --- |
| `id` | string (uuid) | yes |  |
| `brief_date` | string (date) | yes |  |
| `summary` | string | yes |  |
| `recommended_actions` | list of `RecommendedActionRead` | yes |  |
| `created_at` | string (date-time) | yes |  |

#### `DashboardKPIsRead`

| Field | Type | Required | Notes |
| --- | --- | :---: | --- |
| `open_jobs` | integer | yes |  |
| `active_candidates` | integer | yes |  |
| `interviewing` | integer | yes |  |
| `pending_actions` | integer | yes |  |
| `stage_counts` | object | yes |  |

#### `DashboardRead`

| Field | Type | Required | Notes |
| --- | --- | :---: | --- |
| `brief` | `DashboardBriefRead` (or null) | yes |  |
| `kpis` | `DashboardKPIsRead` | yes |  |
| `awaiting_review` | list of `ApplicationWithCandidate` | yes |  |
| `low_applicant_jobs` | list of `LowApplicantJobRead` | yes |  |
| `recent_analyses` | list of `RecentAnalysisRead` | yes |  |
| `recent_workflow_runs` | list of `WorkflowRunRead` | yes |  |
| `pending_drafts` | list of `EmailRead` | yes |  |

#### `DocumentCategory`

One of: `policy`, `benefits`, `procedure`, `other`.

#### `DraftEmailRequest`

| Field | Type | Required | Notes |
| --- | --- | :---: | --- |
| `email_type` | `EmailType` | yes |  |

#### `EmailListResponse`

| Field | Type | Required | Notes |
| --- | --- | :---: | --- |
| `items` | list of `EmailRead` | yes |  |

#### `EmailRead`

| Field | Type | Required | Notes |
| --- | --- | :---: | --- |
| `id` | string (uuid) | yes |  |
| `application_id` | string (uuid) | yes |  |
| `email_type` | string | yes |  |
| `status` | string | yes |  |
| `recipient_email` | string | yes |  |
| `subject` | string | yes |  |
| `body` | string | yes |  |
| `llm_provider` | string (or null) | yes |  |
| `llm_model` | string (or null) | yes |  |
| `prompt_version` | string (or null) | yes |  |
| `sent_at` | string (date-time) (or null) | yes |  |
| `created_at` | string (date-time) | yes |  |
| `updated_at` | string (date-time) | yes |  |

#### `EmailType`

One of: `rejection`, `interview_invitation`, `onboarding_welcome`.

#### `EmployeeRead`

| Field | Type | Required | Notes |
| --- | --- | :---: | --- |
| `id` | string (uuid) | yes |  |
| `first_name` | string | yes |  |
| `last_name` | string | yes |  |
| `email` | string | yes |  |
| `job_title` | string | yes |  |
| `hire_date` | string (date) | yes |  |

#### `EmploymentType`

One of: `full_time`, `part_time`, `contract`, `internship`.

#### `ExperienceFitRead`

| Field | Type | Required | Notes |
| --- | --- | :---: | --- |
| `candidate_relevant_years` | number (or null) |  |  |
| `meets_minimum` | boolean (or null) |  |  |
| `justification` | string (or null) |  |  |

#### `HireWorkflowStatusRead`

| Field | Type | Required | Notes |
| --- | --- | :---: | --- |
| `workflow_run` | `WorkflowRunRead` (or null) | yes |  |
| `employee` | `EmployeeRead` (or null) | yes |  |
| `onboarding_tasks` | list of `OnboardingTaskRead` | yes |  |

#### `JobCreateRequest`

| Field | Type | Required | Notes |
| --- | --- | :---: | --- |
| `title` | string | yes | min length 2; max length 255 |
| `description` | string | yes | min length 1 |
| `employment_type` | `EmploymentType` | yes |  |
| `location` | string (or null) |  | max length 255 |
| `salary_min` | integer (or null) |  | min 0.0 |
| `salary_max` | integer (or null) |  | min 0.0 |
| `salary_currency` | `Currency` |  | default `USD` |
| `required_skills` | list of string |  |  |
| `preferred_skills` | list of string |  |  |
| `min_years_experience` | integer (or null) |  | min 0.0 |

#### `JobListResponse`

| Field | Type | Required | Notes |
| --- | --- | :---: | --- |
| `items` | list of `JobWithStatsRead` | yes |  |
| `total` | integer | yes |  |
| `page` | integer | yes |  |
| `page_size` | integer | yes |  |

#### `JobRead`

| Field | Type | Required | Notes |
| --- | --- | :---: | --- |
| `id` | string (uuid) | yes |  |
| `company_id` | string (uuid) | yes |  |
| `created_by` | string (uuid) (or null) | yes |  |
| `title` | string | yes |  |
| `description` | string | yes |  |
| `employment_type` | `EmploymentType` | yes |  |
| `location` | string (or null) | yes |  |
| `salary_min` | integer (or null) | yes |  |
| `salary_max` | integer (or null) | yes |  |
| `salary_currency` | `Currency` | yes |  |
| `status` | `JobStatus` | yes |  |
| `required_skills` | list of string | yes |  |
| `preferred_skills` | list of string | yes |  |
| `min_years_experience` | integer (or null) | yes |  |
| `created_at` | string (date-time) | yes |  |
| `updated_at` | string (date-time) | yes |  |

#### `JobStatus`

One of: `draft`, `open`, `closed`, `archived`.

#### `JobStatusTransitionRequest`

| Field | Type | Required | Notes |
| --- | --- | :---: | --- |
| `target_status` | `JobStatus` | yes |  |

#### `JobUpdateRequest`

| Field | Type | Required | Notes |
| --- | --- | :---: | --- |
| `title` | string (or null) |  | min length 2; max length 255 |
| `description` | string (or null) |  | min length 1 |
| `employment_type` | `EmploymentType` (or null) |  |  |
| `location` | string (or null) |  | max length 255 |
| `salary_min` | integer (or null) |  | min 0.0 |
| `salary_max` | integer (or null) |  | min 0.0 |
| `salary_currency` | `Currency` (or null) |  |  |
| `required_skills` | list of string (or null) |  |  |
| `preferred_skills` | list of string (or null) |  |  |
| `min_years_experience` | integer (or null) |  | min 0.0 |

#### `JobWithStatsRead`

| Field | Type | Required | Notes |
| --- | --- | :---: | --- |
| `id` | string (uuid) | yes |  |
| `company_id` | string (uuid) | yes |  |
| `created_by` | string (uuid) (or null) | yes |  |
| `title` | string | yes |  |
| `description` | string | yes |  |
| `employment_type` | `EmploymentType` | yes |  |
| `location` | string (or null) | yes |  |
| `salary_min` | integer (or null) | yes |  |
| `salary_max` | integer (or null) | yes |  |
| `salary_currency` | `Currency` | yes |  |
| `status` | `JobStatus` | yes |  |
| `required_skills` | list of string | yes |  |
| `preferred_skills` | list of string | yes |  |
| `min_years_experience` | integer (or null) | yes |  |
| `created_at` | string (date-time) | yes |  |
| `updated_at` | string (date-time) | yes |  |
| `applicant_count` | integer | yes |  |
| `stage_counts` | object | yes |  |

#### `KnowledgeCitationRead`

| Field | Type | Required | Notes |
| --- | --- | :---: | --- |
| `document_id` | string (uuid) | yes |  |
| `document_title` | string | yes |  |
| `chunk_id` | string (uuid) | yes |  |
| `excerpt` | string | yes |  |

#### `KnowledgeDocumentListResponse`

| Field | Type | Required | Notes |
| --- | --- | :---: | --- |
| `items` | list of `KnowledgeDocumentRead` | yes |  |
| `total` | integer | yes |  |
| `page` | integer | yes |  |
| `page_size` | integer | yes |  |

#### `KnowledgeDocumentRead`

| Field | Type | Required | Notes |
| --- | --- | :---: | --- |
| `id` | string (uuid) | yes |  |
| `title` | string | yes |  |
| `category` | string | yes |  |
| `original_filename` | string | yes |  |
| `content_type` | string | yes |  |
| `file_size_bytes` | integer | yes |  |
| `status` | string | yes |  |
| `error_message` | string (or null) | yes |  |
| `embedding_model` | string (or null) | yes |  |
| `embedding_dimension` | integer (or null) | yes |  |
| `embedding_version` | string (or null) | yes |  |
| `last_processed_at` | string (date-time) (or null) | yes |  |
| `created_at` | string (date-time) | yes |  |
| `updated_at` | string (date-time) | yes |  |

#### `LeaveBalanceRead`

| Field | Type | Required | Notes |
| --- | --- | :---: | --- |
| `year` | integer | yes |  |
| `annual_allotment` | integer | yes |  |
| `days_used` | integer | yes |  |
| `days_remaining` | integer | yes |  |

#### `LeaveRequestCreateRequest`

| Field | Type | Required | Notes |
| --- | --- | :---: | --- |
| `start_date` | string (date) | yes |  |
| `end_date` | string (date) | yes |  |
| `leave_type` | `LeaveType` | yes |  |
| `reason` | string (or null) |  |  |

#### `LeaveRequestListResponse`

| Field | Type | Required | Notes |
| --- | --- | :---: | --- |
| `items` | list of `LeaveRequestRead` | yes |  |
| `total` | integer | yes |  |
| `page` | integer | yes |  |
| `page_size` | integer | yes |  |

#### `LeaveRequestPipelineListResponse`

| Field | Type | Required | Notes |
| --- | --- | :---: | --- |
| `items` | list of `LeaveRequestWithEmployee` | yes |  |
| `total` | integer | yes |  |
| `page` | integer | yes |  |
| `page_size` | integer | yes |  |

#### `LeaveRequestRead`

| Field | Type | Required | Notes |
| --- | --- | :---: | --- |
| `id` | string (uuid) | yes |  |
| `employee_id` | string (uuid) | yes |  |
| `company_id` | string (uuid) | yes |  |
| `start_date` | string (date) | yes |  |
| `end_date` | string (date) | yes |  |
| `leave_type` | `LeaveType` | yes |  |
| `reason` | string (or null) | yes |  |
| `status` | `LeaveRequestStatus` | yes |  |
| `reviewed_by` | string (uuid) (or null) | yes |  |
| `reviewed_at` | string (date-time) (or null) | yes |  |
| `created_at` | string (date-time) | yes |  |
| `updated_at` | string (date-time) | yes |  |

#### `LeaveRequestStatus`

One of: `pending`, `approved`, `rejected`, `cancelled`.

#### `LeaveRequestWithEmployee`

| Field | Type | Required | Notes |
| --- | --- | :---: | --- |
| `id` | string (uuid) | yes |  |
| `employee_id` | string (uuid) | yes |  |
| `company_id` | string (uuid) | yes |  |
| `start_date` | string (date) | yes |  |
| `end_date` | string (date) | yes |  |
| `leave_type` | `LeaveType` | yes |  |
| `reason` | string (or null) | yes |  |
| `status` | `LeaveRequestStatus` | yes |  |
| `reviewed_by` | string (uuid) (or null) | yes |  |
| `reviewed_at` | string (date-time) (or null) | yes |  |
| `created_at` | string (date-time) | yes |  |
| `updated_at` | string (date-time) | yes |  |
| `employee` | `EmployeeRead` | yes |  |

#### `LeaveType`

One of: `vacation`, `sick`, `personal`.

#### `LoginRequest`

| Field | Type | Required | Notes |
| --- | --- | :---: | --- |
| `email` | string (email) | yes |  |
| `password` | string | yes |  |

#### `LowApplicantJobRead`

| Field | Type | Required | Notes |
| --- | --- | :---: | --- |
| `job_id` | string (uuid) | yes |  |
| `title` | string | yes |  |
| `applicant_count` | integer | yes |  |

#### `OnboardingTaskRead`

| Field | Type | Required | Notes |
| --- | --- | :---: | --- |
| `id` | string (uuid) | yes |  |
| `title` | string | yes |  |
| `completed` | boolean | yes |  |

#### `PipelineListResponse`

| Field | Type | Required | Notes |
| --- | --- | :---: | --- |
| `items` | list of `ApplicationWithScore` | yes |  |
| `total` | integer | yes |  |
| `page` | integer | yes |  |
| `page_size` | integer | yes |  |

#### `PublicJobListResponse`

| Field | Type | Required | Notes |
| --- | --- | :---: | --- |
| `items` | list of `PublicJobRead` | yes |  |
| `total` | integer | yes |  |
| `page` | integer | yes |  |
| `page_size` | integer | yes |  |

#### `PublicJobRead`

| Field | Type | Required | Notes |
| --- | --- | :---: | --- |
| `id` | string (uuid) | yes |  |
| `company_name` | string | yes |  |
| `title` | string | yes |  |
| `description` | string | yes |  |
| `employment_type` | `EmploymentType` | yes |  |
| `location` | string (or null) | yes |  |
| `salary_min` | integer (or null) | yes |  |
| `salary_max` | integer (or null) | yes |  |
| `salary_currency` | `Currency` | yes |  |
| `required_skills` | list of string | yes |  |
| `preferred_skills` | list of string | yes |  |
| `min_years_experience` | integer (or null) | yes |  |
| `created_at` | string (date-time) | yes |  |

#### `RecentAnalysisRead`

| Field | Type | Required | Notes |
| --- | --- | :---: | --- |
| `analysis_id` | string (uuid) | yes |  |
| `application_id` | string (uuid) | yes |  |
| `candidate_name` | string | yes |  |
| `job_title` | string | yes |  |
| `overall_score` | number (or null) | yes |  |
| `analyzed_at` | string (date-time) (or null) | yes |  |

#### `RecommendedActionRead`

| Field | Type | Required | Notes |
| --- | --- | :---: | --- |
| `label` | string | yes |  |
| `application_id` | string (or null) | yes |  |

#### `RegisterCandidateRequest`

| Field | Type | Required | Notes |
| --- | --- | :---: | --- |
| `first_name` | string | yes | min length 1; max length 100 |
| `last_name` | string | yes | min length 1; max length 100 |
| `email` | string (email) | yes |  |
| `password` | string | yes | min length 8; max length 128 |

#### `RegisterCompanyRequest`

| Field | Type | Required | Notes |
| --- | --- | :---: | --- |
| `company_name` | string | yes | min length 2; max length 255 |
| `admin_first_name` | string | yes | min length 1; max length 100 |
| `admin_last_name` | string | yes | min length 1; max length 100 |
| `email` | string (email) | yes |  |
| `password` | string | yes | min length 8; max length 128 |

#### `ResumeAnalysisHistoryResponse`

| Field | Type | Required | Notes |
| --- | --- | :---: | --- |
| `items` | list of `ResumeAnalysisRead` | yes |  |

#### `ResumeAnalysisRead`

| Field | Type | Required | Notes |
| --- | --- | :---: | --- |
| `id` | string (uuid) | yes |  |
| `application_id` | string (uuid) | yes |  |
| `parsed_resume_id` | string (uuid) | yes |  |
| `status` | string | yes |  |
| `overall_score` | number (or null) | yes |  |
| `required_skills_score_pct` | number (or null) | yes |  |
| `preferred_skills_score_pct` | number (or null) | yes |  |
| `experience_score_pct` | number (or null) | yes |  |
| `scoring_algorithm_version` | string (or null) | yes |  |
| `required_skills_result` | list of `SkillMatchRead` | yes |  |
| `preferred_skills_result` | list of `SkillMatchRead` | yes |  |
| `experience_fit` | `ExperienceFitRead` (or null) | yes |  |
| `matched_skills` | list of string | yes |  |
| `missing_skills` | list of string | yes |  |
| `strengths` | list of string | yes |  |
| `potential_concerns` | list of string | yes |  |
| `explanation` | string (or null) | yes |  |
| `llm_provider` | string (or null) | yes |  |
| `llm_model` | string (or null) | yes |  |
| `prompt_version` | string (or null) | yes |  |
| `error_message` | string (or null) | yes |  |
| `analyzed_at` | string (date-time) (or null) | yes |  |
| `created_at` | string (date-time) | yes |  |

#### `ResumeRead`

| Field | Type | Required | Notes |
| --- | --- | :---: | --- |
| `id` | string (uuid) | yes |  |
| `candidate_id` | string (uuid) | yes |  |
| `original_filename` | string | yes |  |
| `content_type` | string | yes |  |
| `file_size_bytes` | integer | yes |  |
| `status` | string | yes |  |
| `parse_error` | string (or null) | yes |  |
| `created_at` | string (date-time) | yes |  |

#### `SkillMatchRead`

| Field | Type | Required | Notes |
| --- | --- | :---: | --- |
| `skill` | string | yes |  |
| `match_state` | string | yes |  |
| `evidence` | string (or null) | yes |  |

#### `TokenResponse`

| Field | Type | Required | Notes |
| --- | --- | :---: | --- |
| `access_token` | string | yes |  |
| `token_type` | string |  | default `bearer` |
| `expires_in` | integer | yes |  |
| `user` | `UserRead` | yes |  |

#### `UpdateEmailRequest`

| Field | Type | Required | Notes |
| --- | --- | :---: | --- |
| `subject` | string | yes | min length 1; max length 255 |
| `body` | string | yes | min length 1 |

#### `UserRead`

| Field | Type | Required | Notes |
| --- | --- | :---: | --- |
| `id` | string (uuid) | yes |  |
| `company_id` | string (uuid) (or null) | yes |  |
| `account_type` | `AccountType` | yes |  |
| `email` | string | yes |  |
| `first_name` | string | yes |  |
| `last_name` | string | yes |  |
| `avatar_url` | string (or null) | yes |  |
| `status` | `UserStatus` | yes |  |
| `roles` | list of string | yes |  |
| `created_at` | string (date-time) | yes |  |

#### `UserStatus`

One of: `active`, `invited`, `disabled`.

#### `WorkflowRunRead`

| Field | Type | Required | Notes |
| --- | --- | :---: | --- |
| `id` | string (uuid) | yes |  |
| `workflow_name` | string | yes |  |
| `status` | string | yes |  |
| `completed_steps` | list of string | yes |  |
| `failed_step` | string (or null) | yes |  |
| `error` | string (or null) | yes |  |
| `created_at` | string (date-time) | yes |  |
