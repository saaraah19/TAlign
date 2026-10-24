# 11 — Roadmap and known limits

This document is the honest ledger: what Talign deliberately does not do, the defects and rough edges that are known, and what is planned next. Every item says how it is known (confirmed on a running stack, or found by reading the code) and where the evidence is, so that nothing here has to be taken on trust.

---

## 1. What is built

Talign is built as an MVP in vertical slices, each delivering a working product end to end: company and candidate accounts with role-based access; jobs with a controlled lifecycle and a public board; applications and a pipeline; **Resume Intelligence** (explainable, versioned alignment analysis); email drafting; a company **Knowledge Center** answering policy questions with citations; the **dashboard** with a daily brief; a **hire workflow** that converts a candidate into an employee in place; an **employee** experience with leave requests and approvals; and **Compass**, the single role-aware entry point to the AI. Documents 03 and 07 describe each in full.

---

## 2. Deliberately not built

The Product Book described a larger product. The MVP rule was that every feature must be polished or left out, and that a feature outside the MVP is explained, not silently added. These are the items left out on purpose:

| Product Book idea | Status | Why it is outside the MVP (what it would require) |
| --- | --- | --- |
| Analytics and an HR-director view (hiring velocity, time to hire, recruiter workload) | Not built | The dashboard covers "what needs attention"; analytics needs history over time that a demo world does not have |
| Notifications centre | Not built | Needs either email integration or a real-time channel; neither is in the MVP |
| Interview scheduling and AI interview kits | Not built | Needs calendar integration and a fifth agent; out of MVP scope |
| Candidate comparison and the "Decision Workspace" | Not built | A strong idea, deferred so the single-candidate experience could be finished well |
| Real email sending | Not built, by design | Every email is a reviewable draft. "Mark as sent" only records that a human sent it elsewhere. This keeps a human in the loop and avoids a deliverability project |
| Rediscovery of past candidates | Not built | Needs enough history to be meaningful |
| ⌘K as a command palette that performs actions | Not built | The ⌘K panel asks questions only; navigation by command was deferred |
| An "AI Center" page | Removed from the plan | The Product Book itself decided AI should be everywhere, not a separate module |
| A dedicated vector database, Celery or Temporal, an OpenAI or Anthropic provider | Not built | pgvector inside PostgreSQL, in-process background tasks, and Gemini alone are enough for the MVP |
| Multi-company employment | Not supported | A converted employee account belongs to one company and can no longer apply elsewhere |
| A manager hierarchy | Not built | Leave approval and pipeline access are company-wide by role, a deliberate simplification |

---

## 3. Known defects and rough edges

Each item is numbered so it can be referred to. **Confirmed** means it was reproduced on a running backend against a real database; **From the code** means it follows from reading the code and has not been reproduced in a browser.

### Defects

1. **Regenerating a hired candidate's welcome email fails.** *Confirmed.* The **Regenerate** button on the welcome-email draft (created by the hire workflow) makes the server answer `500` with `Unknown email_type: 'onboarding_welcome'`. The regenerate path only knows how to write rejection and interview-invitation emails. Editing and marking that draft as sent work. The button is visible to recruiters, so the failure is reachable. *Fix:* give the regenerate path the welcome-email case, or hide the button for that type.
2. **Admin-created employees cannot use leave.** *Confirmed.* An account created with the `employee` role through the add-user endpoint has no employee record, so every leave call answers `404` "No employee record found for this account." Only the hire workflow creates the record. *Fix:* either create the record when an employee account is added, or remove `employee` from the roles that endpoint accepts.
3. **The access token was never renewed during a session. Fixed.** *Was: from the code.* The API client now renews an expired token once and retries, sharing one renewal between simultaneous requests; if the renewal fails the session ends cleanly. Covered by unit tests that were mutation-checked.
4. **The route-protection cookie assumed one site. Resolved by design.** *Was: from the code.* The frontend's middleware no longer exists: the web app is a static site that forwards `/api/*` to the API, so the browser only ever uses one address and the sign-in cookie belongs to it. Browser-checked behind a server that applies Render's documented rules; the real forwarding on Render is a live check (document 09).

### Gaps in the interface

5. **There is no screen to edit a job.** *From the code.* The API supports it, but the title, description and scoring criteria cannot be changed from the interface after creation. Because the criteria drive the score, this matters.
6. **There is no screen to add teammates.** *From the code.* Adding a recruiter or another user is available only through the API. The company registration page nevertheless says "invite your team afterward".
7. **Hiring managers see buttons the server refuses.** *Confirmed.* Apart from "New job" and the knowledge-management controls, the pipeline write controls (advance, reject, draft, regenerate, re-analyze, job status changes) are visible to a hiring manager and answer `403` when used.
8. **The onboarding checklist cannot be completed.** *From the code.* The hire workflow creates four tasks, but no endpoint or screen marks them done.
9. **A rejection email has to be drafted before rejecting.** *Confirmed.* Once an application is `rejected` or `hired`, drafting is refused by the server and disabled in the interface.

### Behaviour worth knowing

10. **The annual leave allowance is a fixed 20 days for every company.** *From the code.* It is not configurable, and it is separate from a company's own policy document: the seeded Helix Health document says 25 days while its employees' balance would show 20.
11. **The daily brief is generated for whoever opens the dashboard first each day**, and the person's first name is part of its prompt, so the cached text may be written for that person and shown to the rest of the company's staff. *From the code; not observed with a real model.*
12. **"Pending actions" on the dashboard cannot exceed twenty**, because it adds two lists that are each capped at ten. *From the code.*
13. **Scanned (image-only) PDFs cannot be analysed.** *From the code.* There is no OCR; the resume is marked unreadable and the candidate is told to upload a text-based file.
14. **Background jobs are lost if the process restarts mid-job.** *From the code.* An interrupted analysis can be re-run and a document re-indexed, but nothing retries automatically.
15. **The login throttle and background tasks assume a single instance.** *From the code.*
16. **Fairness safeguards are instructions to the model, not a guarantee.** The prompts forbid using protected characteristics and never receive the candidate's name or email, but resume text often contains a name, and no bias evaluation has been done.

### Housekeeping

17. **`langgraph` is declared as a dependency but never imported.** *Confirmed by search.* Only LangChain's core and Google packages are used.
18. **The LLM settings overpromise.** `LLM_PROVIDER` accepts `openai` and `anthropic`, and a comment in `.env.example` says switching needs only a setting change. In fact only Gemini works.
19. **Some comments and docstrings are stale.** For example `models/employee.py` still says `user_id` is always empty, `OnboardingTask` says the employee portal is out of scope, a comment in `knowledge_query_service.py` says only recruiting staff may use it (employees may), `compass/intent.py` is defined but never used, and one migration carries an "UPDATE THIS" comment. `PROJECT_STATUS.md`, which predated all of this, was retired together with the documentation work (the original slice notes and earlier handovers now live in `docs/history/`).
20. **One architectural rule is not machine-checked.** "Only `core/llm_provider.py` may import an LLM library" is true today but no test would fail if it were broken.
21. **Two lint findings** exist in `backend/scripts/seed_demo.py` (not run by CI).

### Verification gaps and hosting realities

22. **The audit for the "MissingGreenlet" bug class is finished. No instance remains on the API's update paths.** Three instances were found and fixed earlier (add-user, leave approval and cancellation, the public job list). A repeatable script, `tools/sandbox_e2e/audit_update_paths.py`, now exercises every data-changing endpoint against a real PostgreSQL: 33 calls, no server error, none in the log, including the job-update route and the email edit and regenerate routes that had never been run on a real database. Ten models are still exposed to the *possibility* (they define `updated_at` in the affected way), so any **new** update path should be added to that script; see document 08.
23. **Quality of the AI output has not been evaluated on a real run.** The seeded resumes are designed to produce a spread of scores, but that spread has never been seen, because development ran with a stand-in for the model.
24. **Real-browser behaviour, mobile layouts and the first GitHub Actions run have not been verified.**

25. **Free hosting has a cost the application can only soften.** *Documented by Render.* On the free plan the API sleeps after 15 idle minutes and takes about a minute to wake (the web app shows a "waking up" screen and keeps the visitor signed in); free instance hours are limited, so the API must not be kept awake with pings; and the database expires after 30 days, so the demo needs a new database and a re-seed monthly. Document 09 has the calendar note.
26. **Uploaded files do not survive a restart on the free plan.** *From the code, with the consequence confirmed by a test.* Resume files are never read back, so nothing is lost there. Re-indexing a document needs its file; when it is gone the request now fails with a clear message and the existing search index is left untouched. Persistent storage is still not implemented.
27. **Render's forwarding is unverified.** That Render's static-site forwarding passes the sign-in cookie in both directions, and how it answers while the API is still asleep, can only be checked on Render. The application is built not to depend on the second (any timeout is treated as "still waking").

---

## 4. What happens next

The order below is the order that has been agreed.

1. **Documentation** (this work): the documents in `docs/` and a detailed README with screenshots of the application running through realistic scenarios.
2. **Going online**, described in document 09. The work is done and tested as far as it can be without Render: a static web app that never sleeps, an API production image that migrates on start, the token renewal, the "waking up" screen, a `render.yaml`, and the live checks written down. What remains is running it on Render and working through those checks.
3. **Fixing the issues above**, starting with the two confirmed defects (items 1 and 2), then the interface gaps and the housekeeping. The database audit (item 22) is done.

Beyond that, if the project continued, the natural next steps are the ones the Product Book already names: analytics for the HR director, candidate comparison, interview scheduling, a real job queue, and email integration. Each would be its own slice, scoped and agreed before any code is written.
