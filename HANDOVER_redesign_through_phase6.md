# Handover — UI/UX redesign through Phase 6

Supersedes the Phase 3, 4 and 5 handovers (this file contains all of them). Read CLAUDE.md first, then
inspect the real repo from the attached zip before touching anything.

## State
MVP (Slices 0-9) and the V2 Employee Portal are complete and live-verified.
Redesign Phases 1-6 are done (the planned redesign is complete): landing, design system + auth, Dashboard,
Jobs + Kanban, candidate workspace (4), Knowledge Center + leave approval (5), global Compass panel + empty
states + toasts/skeletons (6).
Verified in the build sandbox: 282/282 backend tests, clean `tsc --noEmit`.
`next build` cannot complete in the sandbox (Inter needs fonts.googleapis.com)
— unchanged known limitation. Phases 4, 5 and 6 were delivered together and are NOT yet live-tested by Sarah
in a browser — treat any bug she reports as real even with green tests.

## Phase 4 — what changed (frontend only, zero backend changes)
Page `pipeline/[id]/page.tsx` is now a two-column workspace: main column
(Resume Intelligence, Communication) + a right rail (Pipeline stage and
actions, Compass, Hire workflow, Activity). The rail is sticky and scrolls
on its own on large screens; everything stacks on mobile.

- Score: `ScoreGauge` ring (animated fill) + `DimensionBars` (required /
  preferred / experience %), bands 80/60 matching the Kanban card colours
  (`features/applications/lib/score.ts`).
- `ExperienceFitCard` surfaces `experience_fit`, returned by the backend
  but never displayed before.
- `SkillEvidenceList`: required and preferred skills with state icons,
  evidence text, "N of M matched", collapsed beyond 6 rows.
- `Insights`: strengths / concerns side by side. Dark "Compass assessment"
  card for the explanation (same visual language as the Dashboard brief).
- `StageJourney` + `StageActions`: stage stepper, advance button, and an
  inline two-click confirmation for Reject (terminal action).
- `CandidateActivity`: feed of real timestamped events only (application
  received, analysis, emails drafted/sent, hire workflow), built from
  caches the panels already fill.
- `EmailDraftCard` is now a composer (To / Subject / body; read-only
  preview once sent). Buttons keep the honest "Mark as sent" wording and
  a note that Talign does not send email.
- `Badge` primitive added; `CompassAsk` restyled (shared by Knowledge,
  portal/leave and the candidate's own application page) with an opt-in
  `suggestions` prop; `HireWorkflowPanel` and its status badge restyled.

## Deliberate decisions to keep
- No stage-by-stage dates: the backend stores current status only, no
  transition history. A real history/audit table would be a new feature,
  not design work — propose it separately if wanted.
- Compass suggestions on a candidate are limited to what `explain_analysis`
  can answer (stored analysis only). "Suggest interview questions" was
  rejected: that belongs to the V2 Interview Agent.
- No modal system yet; Reject uses an inline confirm until Phase 6.

- Phase 6: global Compass command panel (build the real thing or keep the
  honest `/knowledge` link), empty-state pass, skeletons/toasts/modals.
  Phase 4 added local skeleton/spinner states only on the candidate page.
- Also still using old gray-* classes: `ApplicationStatusBadge`, the
  candidate's own `applications/[id]` page, `PipelineView` (legacy list).

## Phase 5 — what changed (frontend only, zero backend changes)
Knowledge Center (`/knowledge`): one `KnowledgeCenter` component fetches
once (page_size 100, the backend maximum) and renders four honest states:
loading skeleton; zero documents (designed empty state, with the upload form
inline for admins, an "ask an admin" note for others); documents but none
ready (explains whether they're processing or all failed); normal. Normal =
summary line (real counts), `CompassHero` (dark panel, Compass centerpiece),
and `DocumentList` grouped by category with filter chips whose counts come
from the same fetched documents. If total > fetched, a note says so.
- Compass starter questions are built from real ready-document titles
  ("What does “X” cover?"), so every one is answerable. The hero only
  appears when at least one document is `ready`.
- `DocumentRow`: file-type tile, real size, relative updated time, status
  badge, Reindex, and Delete with an inline two-click confirm.
- `DocumentUpload` restyled (Input primitive, dropzone-style file label),
  gained an optional `onUploaded` callback; `DocumentList` is now purely
  presentational (props: documents, canManage). `CompassAsk` gained
  `showHeader` (default true).
Leave requests (`/leave-requests`, the approval queue): status tabs with
real counts via `useLeaveRequestCounts` — four `page_size=1` calls reading
the backend's filtered `total`, no new endpoint — a "N requests waiting"
sentence, request rows (avatar, type badge, date range, day count, reason),
Approve in one click, Reject with inline confirm, per-tab designed empty
states, skeleton loading, and a Previous/Next pager (the old queue silently
hid anything past 20 rows; it also steps back a page if you act on the last
row of the last page). Day count uses inclusive calendar days, the exact
formula the backend uses for leave balance. Dates are parsed as local days
(tested in UTC, Los Angeles, Algiers) to avoid off-by-one shifts.
The employee-side leave page (`portal/leave`) was NOT touched.

## Phase 6 — what changed (frontend only, zero backend changes)
**Global Compass panel (Cmd/Ctrl+K).** `src/components/compass-panel/` (the
app-shell level, NOT the compass feature: it must read the knowledge feature
and the compass feature already depends on knowledge's consumers — putting it
in `compass` would create an import cycle). A native `<dialog>` opened with
`showModal()` (focus trap, Esc, backdrop, inert page for free). Mounted by
`CompassPanelProvider` in `(protected)/layout.tsx`; triggers: NavBar button,
dashboard header button, the shortcut.
- It is honest about what Compass can do (mirrors
  `Compass._resolve_capability_for_role`): staff get "Company policies" always
  and "This candidate" when on `/pipeline/{uuid}`; plain employees get company
  policies; candidates get ONLY "My application" on `/applications/{uuid}` and
  are not offered the panel anywhere else (no policy access exists for them).
  Rules live in `compass-scope.ts` (pure function, unit-tested matrix).
- Company scope offers suggestions from real ready-document titles; with no
  ready documents it shows an honest empty state linking to /knowledge and no
  input box. The body only mounts while open: closing resets the conversation.
- Real bug found by testing and fixed: React's `autoFocus` runs while the
  dialog is still closed, and `showModal()` then focuses the close button.
  `CompassPanel` now focuses the input right after `showModal()`.
- `CompassAsk` gained `autoFocus` and `bare`; suggestion lists moved to
  `features/compass/suggestions.ts` (shared by the candidate page, the panel
  and Knowledge).
**Primitives** (`components/ui/`): `Skeleton`, `EmptyState` (what is missing /
why / what next), `toast.tsx` (`ToastProvider` mounted in `app/providers.tsx`
so public pages get it; `useToast()` throws outside a provider), and
`buttonClasses()` exported from `button.tsx` for link-styled buttons (the old
`<Link><Button/></Link>` pattern nested interactive elements).
**Toasts** are for successes (stage moves, rejections, emails drafted/sent,
analysis restarted, leave approve/reject/cancel, document upload/delete/
reindex, job created/transitioned/deleted, application submitted, resume
attached). Errors stay inline next to the thing that failed; the one
exception is cancelling a leave request from a list, which replaced a browser
`alert()` with `toast.error`.
**Skeletons** replaced every plain "Loading…" (protected layout, pipeline,
applications/[id], careers pages, job detail, job list, Kanban columns, my
applications/leave lists).
**Empty states**: new/upgraded for My applications (with a Browse jobs
action), My leave requests, Careers, Dashboard activity feed, job list and
leave queue (now on the primitive), and Kanban columns (stage-specific hints).

## Known gaps / deliberate non-goals
- No history in the panel across closes; no closing animation (native dialog
  closes instantly; opening has a short fade).
- `PipelineView` (legacy list) is dead code — nothing imports it. Delete it
  deliberately or leave it; it was not touched.
- Still on old gray-* styling: `ApplicationStatusBadge`, candidate-side
  `applications/[id]`, careers/apply pages, employee portal leave components
  (balance card, request form). `LeaveRequestForm` keeps its own inline
  success message instead of a toast.
- NavBar itself (uses the app router) was not rendered in tests; the provider
  and panel it drives were.

## Verification done on Phases 4-6
`tsc --noEmit` clean; 282/282 backend tests (untouched). 81 jsdom interaction
checks (a throwaway harness, not committed): toast timing/cap/dismiss; every
inline confirm (stage reject, document delete, leave reject) including "no
network call until confirmed"; panel open/close/backdrop/Esc/scroll lock/
focus; scope switching; the scope matrix per role and path; the real
AuthProvider driving the provider (Ctrl/Cmd+K toggle, inert for candidates,
closes on navigation); KnowledgeCenter in all five states; the leave queue
pager clamp (verified the test FAILS if the fix is removed); email composer.
Earlier static-render checks covered Phase 4 score/stage/skill components.
NOT verified: real-browser layout and responsive behaviour, native `<dialog>`
focus behaviour in a real browser (jsdom only emulates it), `next build`
(Inter font fetch blocked in the sandbox), visual polish — Sarah's live test.

## Possible next steps (not started, none are scheduled)
Restyle the remaining gray-* pages; remove `PipelineView`; an optional
"recent conversations" memory for the panel; real per-stage history (needs a
backend transition-history table — a feature, not design).

## Environment reminders
Windows/PowerShell, Docker Compose only; frontend rebuild suffices for this
work (no backend or migration changes). Ruff/mypy baseline noise (B008,
UUID|None) is known — do not drive-by fix.

## Post-delivery fix — candidate career page returned 500 (found by Sarah's live test)
Symptom: `/careers` showed nothing; the browser console reported a CORS error.
Real cause: `GET /api/v1/public/jobs` returned 500. In Phase 3 `JobListResponse`
was changed to carry `JobWithStatsRead` items (applicant_count, stage_counts) for
the recruiter Jobs page, but `public_jobs.py` still built that response from plain
`JobRead` objects, so every call failed Pydantic validation. The CORS message was
only a symptom: an unhandled 500 never passes through the CORS middleware.
Fix (backend + frontend): new `PublicJobListResponse` (items are plain `JobRead`,
no stats — applicant counts are recruiter-only data and must not reach the public
endpoint); `public_jobs.py` uses it; frontend `publicJobsApi.list` is typed
`PublicJobListResponse`. New `tests/test_public_jobs_api.py` drives the real route
(only the DB session and the service call are replaced) and asserts 200, that the
stats fields are absent, and that the schema is structurally free of them. Verified
it reproduces the exact error from the logs on the old code. 285/285 backend tests.
Lesson: the service-level tests mock their repositories and never exercise a
route's response model, so a response-schema change can break an endpoint silently.
When changing a shared response schema, grep every route using it, and prefer a
route-level test (see test_public_jobs_api.py for the pattern). mypy had flagged
this mismatch all along (arg-type on `items=`) — it is worth reading its output on
`app/api/` after schema changes even though the rest of its output is baseline noise.
**Needs a full rebuild** (backend change): `docker compose down` then
`docker compose up --build`.
