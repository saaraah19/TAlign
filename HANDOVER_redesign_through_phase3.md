# Handover — Talign redesign, through Phase 3

Read this before doing anything else. Written after a sandbox reset wiped the
working container mid-session; everything below was reconstructed from the
conversation transcript and re-verified from scratch (282/282 backend tests,
clean `tsc --noEmit`), so it's trustworthy, not just "probably fine."

## What this zip is

Every file changed across **five pieces of work**, done in this order, on top
of Sarah's repo as it stood right after Sub-slice 9c (Leave Management):

1. **Hire → employee portal access.** When an Application moves to HIRED,
   `HireCandidateWorkflow` now runs a 4th step that converts the candidate's
   own existing account (same email/password) into an employee account in
   place — see `AuthService.convert_candidate_to_employee`. No invite-token
   system exists or was built; there was nothing to link, because a
   candidate IS a User row already (no separate Candidate table). Also
   fixed two RBAC gates (`Compass._resolve_capability_for_role`, the
   `knowledge_query` capability, `/api/v1/knowledge`'s `_READ_ROLES`) that
   had deliberately excluded `Role.EMPLOYEE` before the Employee Portal
   existed to use them.
2. **Dashboard employee-view bug fix.** `/dashboard` is the shared landing
   page for every account type; an early version of the employee-gating
   logic accidentally also showed the recruiter dashboard to employees
   (`account_type === "internal"` matches both). Fixed by gating on roles
   via a new `lib/roles.ts` (`isPlainEmployee`), not account_type.
3. **Landing page redesign.** Sarah's own detailed brief. New design tokens
   (`ink`/`paper`/`accent`/`line` in `tailwind.config.js`), Inter via
   `next/font/google`, a `components/landing/` folder (nav, hero with a
   `CompassPreview` mock chat UI, three hand-drawn capability icons — no
   icon library added, a merged "how it works"/"one identity two chapters"
   journey timeline, an AI-vs-Human section, footer). The old landing page
   was a bare Slice-4 health-check screen; that's now fully gone from the
   public page (removed, not hidden-on-error, per her own instruction).
4. **Phase 1 of the authenticated-app redesign: design system + auth +
   nav.** `components/ui/{button,input,ai-mark,avatar,card}.tsx`, a shared
   `auth-split-layout.tsx` (reuses the landing page's own `CompassPreview`
   — literally the same component, not a copy), Login and candidate-signup
   rebuilt on it, company signup rebuilt as a real 2-step flow (not
   inventing fields — just regrouping the 5 that existed), NavBar restyled
   (kept as a top nav, not switched to a sidebar — Sarah said she likes its
   simplicity).
5. **Phase 2 (Dashboard) and Phase 3 (Jobs + Pipeline) of the same
   redesign.** These needed real backend work first, not fake frontend
   numbers — see "Backend additions" below. Dashboard rebuilt as
   `DashboardHeader` + `KpiRow` + a dark `DailyBriefCard` + `HiringFunnel` +
   merged `AttentionNeeded` + merged human-readable `ActivityFeed` (6 old
   raw-list components deleted). Jobs rebuilt with real per-job stats,
   search/tabs, a designed empty state. Pipeline rebuilt as a genuine
   Kanban board — **not free drag-and-drop**: the backend's
   `ApplicationService._ALLOWED_TRANSITIONS` is strictly forward-only plus
   reject, so each card gets an "Advance →" button to its one legal next
   stage instead of letting you drop it anywhere. While fixing workflow-run
   display for the activity feed, caught and fixed a real pre-existing
   drift bug: the frontend's `HIRE_WORKFLOW_STEP_LABELS` only listed 3
   steps, missing `grant_portal_access` from work item #1 above.

## Backend additions (Phase 2 + 3) — the aggregation logic

None of this existed before; the Jobs/Pipeline/Dashboard UIs needed real
numbers, so:

- `JobRepository.count_open` — Dashboard's "Open roles" KPI
- `ApplicationRepository.count_by_status_for_company` — one GROUP BY query
  for the whole hiring funnel (Dashboard)
- `ApplicationRepository.count_by_status_grouped_by_job` — same idea, one
  level finer (Jobs list per-card stats)
- `ResumeAnalysisRepository.get_latest_completed_scores` — Postgres
  `DISTINCT ON`, one query for every Pipeline card's match score
- `DashboardService`, `JobService`, `ApplicationService` all extended
  accordingly; `JobRead`/`ApplicationWithCandidate` grew
  `JobWithStatsRead`/`ApplicationWithScore` subclasses, since the new
  fields aren't real columns and can't come from a plain
  `model_validate(row)`
- Along the way, fixed two services (`AuthService`, `JobService`) that
  didn't support the project's own stated convention of optional
  constructor-injected repositories — needed it for testing, fixed it
  properly rather than reaching into private attributes in tests

9 new backend test files total across all five pieces of work. All of it is
real, tested logic — nothing in the Dashboard/Jobs/Pipeline numbers is
fabricated frontend data.

## How to apply this

1. Copy every file in this zip into the matching path in the real repo,
   overwriting what's there.
2. **Delete these 7 files — nothing references them anymore, confirmed:**
   - `frontend/src/features/dashboard/components/awaiting-review-section.tsx`
   - `frontend/src/features/dashboard/components/low-applicant-jobs-section.tsx`
   - `frontend/src/features/dashboard/components/recent-analyses-section.tsx`
   - `frontend/src/features/dashboard/components/recent-workflow-runs-section.tsx`
   - `frontend/src/features/dashboard/components/pending-drafts-section.tsx`
   - `frontend/src/features/dashboard/components/section.tsx`
   - `frontend/src/features/applications/components/pipeline-view.tsx`
3. No new migrations — none of this touched the database schema, only
   existing tables via new queries.
4. `docker compose down && docker compose up --build` as always.
5. `npm install` inside the frontend container/image if it doesn't already
   pick up `next/font/google`'s Inter — this needs real internet access to
   fetch the font at build time (works fine in a normal Docker build, just
   couldn't be verified in my own sandboxed container for the same reason
   as before — no access to fonts.googleapis.com there).

## What's verified vs. not

**Verified by me, directly:** 282/282 backend tests passing, `ruff`/`mypy`
clean on every new/changed backend file (only the same pre-existing
baseline noise — B008, one systemic `UUID | None` mypy gap — that's been
confirmed present identically elsewhere in this codebase since Sub-slice
9c), `tsc --noEmit` clean on the whole frontend.

**NOT verified — needs Sarah's own pass, same as every prior slice's
"green tests ≠ working system" lesson:** nobody has looked at any of this
rendered in a real browser yet. Specifically worth checking first:
- The Kanban board's "Advance →" / "Reject" buttons actually calling the
  real transition endpoint and the board re-fetching correctly
- The Jobs list's new per-job stats and the "View pipeline →" link
- The Dashboard's funnel bars and the merged activity feed's relative
  timestamps
- The login/signup split-layout on an actual small screen (mobile
  responsiveness per her brief's item 15 was designed-for via Tailwind
  breakpoints but never visually checked)
- Whether `next/font/google` actually resolves in her real Docker build

## What's explicitly NOT done yet (remaining phases of the redesign brief)

Sarah's full brief had 15 numbered items. Phases 1-3 above cover items
1 (partially — only the primitives Phase 1-3 needed were built; Badge,
Tabs, Modal, Alert, Progress don't exist yet), 2, 3, 4 (partially — KPI
row/Compass briefing/funnel/activity done, but item 4's exact mockup
wording wasn't chased further), 5, 6, 10 (kept as top nav, not the sidebar
her example showed), 14, 15 (Tailwind-responsive, unverified in-browser).

**Not started at all:**
- **Item 7 — Candidate detail page** as an "intelligence workspace"
  (two-column layout, visual alignment-score breakdown, strengths/concerns/
  evidence hierarchy, a real email composer/preview instead of raw text,
  a visual hiring-workflow timeline). This is explicitly Phase 4.
- **Item 8 — Knowledge Center** redesign (document library grouped by
  category, Compass made the centerpiece, example questions, a real
  empty state). Phase 5.
- **Item 9 — Leave requests page** redesign (status tabs, summary counts,
  designed empty state — the backend already supports status filtering,
  this is frontend-only). Phase 5.
- **Item 11 — the global Compass command/search panel** (a ⌘K-style
  "Ask Compass" overlay reachable from anywhere in the shell). Every
  current "Ask Compass" button honestly links to `/knowledge` instead of
  faking this — don't let a future pass silently add a fake non-functional
  button here; this needs the real thing or nothing. Phase 6.
- **Item 12 — a systematic empty-state pass** across every list in the
  product (some lists already got one as part of Phases 1-3 — Jobs,
  Attention Needed, Kanban columns, Leave's own pre-existing one — but
  nobody's gone through checking every single list against the "what's
  missing → why it matters → what's next" template specifically).
- **Item 13 — microinteractions** (skeleton loading states, toast
  notifications, modal transitions). Essentially nothing here yet beyond
  basic hover/focus states and the landing page's one fade-up entrance.

## Project context worth knowing if you're a fresh instance

- This is a portfolio project (`talign-slice4-fixed`), Sarah's own repo,
  not a client project.
- Docker Compose is the only supported way to run it locally — no bare
  `uvicorn`/`npm run dev`. A full rebuild (`down && up --build`) is
  required after any backend/migration change; a plain restart is a
  documented recurring false "my fix isn't working" trap in this project.
- Sandbox resets have now hit this project's working state **twice** —
  once on Sarah's end early on (which is why 9a-2 had to be rediscovered
  and rebuilt as the hire-to-employee-conversion work), and now once on my
  end during this redesign. Package deliverables and write handovers
  proactively; don't accumulate unpackaged work across turns.
- Full memory of this project's history lives in the assistant's own
  memory files (`architecture-decisions.md`, `overview.md`,
  `ways-of-working.md`) if this is a fresh conversation — read those
  before assuming anything about what's been built.
