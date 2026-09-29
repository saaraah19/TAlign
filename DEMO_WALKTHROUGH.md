# Talign — demo walkthrough

A ~10-minute script that touches every major built feature, in an order that
tells a coherent story: a candidate is discovered, scored, hired, and becomes
an employee — all as one continuous identity. Written for showing this to a
recruiter, an interviewer, or recording a portfolio video.

Use two browser windows (or one regular + one incognito) so you can be
logged in as two people at once: **the admin** and **the candidate**.

Before you start: `docker compose up --build`, then seed at least one
company (register one) if you don't already have test data.

---

## Act 1 — Post a job (as admin)

1. Register a company at `/register/company`, or log in if you already have
   one. You land on the **Dashboard** — say out loud that this is Compass's
   Daily Alignment Brief: an LLM-generated summary of what needs attention
   today, backed by real counts (applications awaiting review, low-applicant
   jobs), not a static template.
2. Go to **Jobs → New Job**. Fill in a real-sounding role (e.g. "Backend
   Engineer") with a short description and a few requirements. Publish it.
3. Open `/careers` in the second window (no login needed — this is the
   public job board). Point out this is the same job, live, with zero extra
   work.

**Talking point:** the Dashboard's brief is cached per company per day and
degrades gracefully — if the LLM call fails, the rest of the dashboard still
renders. AI is additive, never a single point of failure.

## Act 2 — Apply and get scored (as candidate)

4. In the second window, apply to the job from `/careers/[id]/apply`. Use a
   real-looking name/email — this identity carries through the entire rest
   of the demo.
5. On the confirmation screen, go to "My applications," open the
   application, and upload a resume (a real PDF works best, but any resume
   text works).
6. Wait a few seconds, then refresh. The status moves through
   Parsing → Analyzing → Complete. Show the **Alignment Score** and its
   breakdown — strengths, gaps, and the reasoning behind the number, not
   just a bare percentage.

**Talking point:** this is the Resume Intelligence Agent — deterministic
parsing, then an LLM extraction step, then a separate LLM alignment-scoring
step against the job's own requirements, each one versioned and stored, so a
prompt change later never silently rewrites history.

## Act 3 — Review the candidate (as admin)

7. Back in the first window, go to **Pipeline**. The application appears
   with its score. Open it — this is the candidate's workspace: resume,
   score breakdown, and a Compass panel that already knows who this
   candidate is and which job they applied to.
8. Ask Compass something like *"What are this candidate's main gaps?"* —
   show that it answers using the actual analysis, not a generic response.
9. Use the draft-email action to generate an interview invitation. Point out
   that Compass only ever produces a **draft** — a human has to review and
   send it. It never emails anyone on its own.
10. Move the application to **Hired**.

**Talking point:** moving to Hired triggers a four-step deterministic
workflow (not another LLM call) — an Employee record is created, an
onboarding checklist is generated, a welcome-email draft is written, and the
candidate's own account is converted into an employee account, in place.
Same email, same password — there was never a second identity to create.

## Act 4 — Become the employee (as candidate, same login)

11. In the second window, log out and log back in with the exact same
    email/password the candidate used to apply. The NavBar has changed —
    Dashboard, Knowledge, Leave — nothing else. This is the same account
    that applied ten minutes ago.
12. Go to **Knowledge**, ask Compass a policy question (upload a short
    policy doc first from the admin side if none exists yet, under
    Knowledge → upload). Show the answer comes with a citation back to the
    real document.
13. Go to **Leave**, show the balance (20 days, fixed annual allotment for
    this MVP), and submit a time-off request.

## Act 5 — Close the loop (as admin)

14. Back in the first window, go to **Leave requests**, approve the pending
    one.
15. Switch back to the employee window, refresh the Leave page — balance
    has dropped by the requested number of days.

**Closing talking point:** approval is company-wide (any admin or hiring
manager can approve anyone's request) rather than routed to an individual
manager — a deliberate simplification, since this codebase has no manager
hierarchy concept at all, not a missing feature.

---

## If you only have 3 minutes

Skip straight to: apply as a candidate (Act 2, steps 4–6) → hire them
(Act 3, step 10) → log back in as the same person and show the employee
view (Act 4, step 11). That's the single most distinctive thing about this
project — one identity, two very different experiences of the same
platform, joined by a deterministic workflow rather than a second login.

## Things that are deliberately NOT built (say so if asked)

- No real email sending anywhere — every "email" is a reviewable draft.
- No manager hierarchy — leave approval is company-wide by design.
- No multi-company employment — a converted employee account can't apply
  as a candidate elsewhere on the platform afterward.
- Payroll, an analytics agent, an interview-scheduling agent, and a
  candidate-rediscovery feature are explicitly out of MVP scope.
