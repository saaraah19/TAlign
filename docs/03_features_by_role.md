# 03 — Features by role

This document walks through what each kind of person can do in Talign, screen by screen, as the application actually behaves. It was written from the frontend pages and components and the backend services they call, and a number of the behaviours below were confirmed by running the real backend against a real database with the seeded demo data. Where behaviour is surprising, limited or unfinished, it says so.

To try everything described here yourself in about ten minutes, use the guided tour in document 10. For who is allowed to do what at the server level, see document 04.

---

## 1. The 18 pages

| Page | Route | Who it is for |
| --- | --- | --- |
| Landing page | `/` | Everyone (no sign-in) |
| Open positions | `/careers` | Everyone (no sign-in) |
| Job detail | `/careers/{id}` | Everyone (no sign-in) |
| Apply | `/careers/{id}/apply` | Candidates |
| Sign in | `/login` | Everyone |
| Register a company | `/register/company` | Someone creating a company workspace |
| Register as a candidate | `/register/candidate` | Job seekers |
| Dashboard | `/dashboard` | Everyone signed in (the content differs by role) |
| My applications | `/applications` | Candidates |
| My application | `/applications/{id}` | Candidates |
| Jobs | `/jobs` | Admin, recruiter, hiring manager |
| New job | `/jobs/new` | Admin, recruiter |
| Job detail (staff) | `/jobs/{id}` | Admin, recruiter, hiring manager |
| Pipeline | `/pipeline` | Admin, recruiter, hiring manager |
| Candidate workspace | `/pipeline/{id}` | Admin, recruiter, hiring manager |
| Knowledge Center | `/knowledge` | Admin, recruiter, hiring manager, employee |
| Leave requests (approvals) | `/leave-requests` | Admin, hiring manager |
| My leave | `/portal/leave` | Employees |

Four things are available on every protected page: the navigation bar (which differs by role), the **Compass panel** (opened with ⌘K or Ctrl+K), notifications of success or failure as small toasts, and sign-out.

---

## 2. Anyone: the public side

**The landing page** is a static marketing page (hero, capabilities, the end-to-end journey, and a section about humans staying in control). It makes no backend call, so a first impression never depends on the server being awake.

**Open positions** lists every `open` job across every company on the platform, newest first, with pagination. Each card shows the title, employer, location, employment type, salary range (if the company published one), the required skills as chips, and how long ago it was posted. This page needs no account.

**A job's page** shows the full description, the salary range with its currency label, the employer, and the required and preferred skills. It has a single call to action, **Apply**, whose behaviour depends on who is looking: a signed-out visitor sees "Create an account to apply" (which opens candidate registration and returns them to the application afterwards); a signed-in *staff* user is told "Only candidate accounts can apply"; a candidate sees "Apply now" and goes to the application page.

---

## 3. Candidates

### Creating an account

A candidate registers with first name, last name, email and a password of at least 8 characters. They belong to no company; their identity is platform-wide, so one account can apply to jobs at many companies.

### Applying

Applying is one page and one click. The candidate chooses a resume that they already uploaded or uploads a new one (PDF, DOCX or plain text, up to 5 MB; the server checks type and size again), then presses **Submit application**. Behind that one click the app creates the application and attaches the resume. Rules enforced by the server: the job must be `open`, the account must be a candidate, and a candidate can apply to a given job only once (a second attempt answers 409).

A resume belongs to the candidate, not to one application, so the same file can be reused for later applications and nothing is re-uploaded.

### Following an application

**My applications** lists each application with its job, employer and current stage. Opening one shows the stage journey (Applied, Screening, Interview, Offer, Hired, or a plain "Not moving forward" if rejected), a resume panel where a different resume can be attached, and the **progress of the automated review**.

That last point is deliberate. The candidate sees only the *progress* of Resume Intelligence ("Parsing resume…", "Analyzing alignment…", "Analysis complete" or "Analysis failed"; nothing at all before a resume is attached), and never a score, a strength, a concern or any other analysis content. This is structural, not cosmetic: no endpoint a candidate can call returns analysis content (a test proves it).

**Compass for candidates** is a small ask box on the application page, offering one suggested question ("What stage is my application at?"). It answers with a templated sentence about the stage. It uses no AI, and it can never discuss company policies or the analysis.

### What a candidate cannot do

There is no interview scheduling, no messaging with the recruiter and no offer-acceptance flow in this version, and no notification of a stage change (the candidate sees the new stage the next time they open the page). A scanned (image-only) PDF cannot be analysed; the candidate is told to upload a text-based file.

### When they are hired

When a recruiter marks the application as Hired, the hire workflow converts this very account into an employee account of the hiring company (section 7). The same email and password now open the employee experience, and the person can no longer apply to other companies' jobs with that login.

---

## 4. Admins and recruiters (the hiring side)

An **admin** is created when someone registers a company; a **recruiter** is added by an admin through the API. On the screens below the two behave identically, except where noted.

### Registering a company

The form takes the company name (at least 2 characters), the admin's first and last name, email, and a password (at least 8 characters). It creates the company and its first admin, signs them in, and opens the dashboard. The page tells them "invite your team afterward", but **there is no screen for adding teammates**: adding a recruiter or another user is currently possible only through the API (the seed script does it that way). This is an unfinished edge of the MVP.

### Dashboard

The dashboard is the recruiter's "what needs my attention" page. From top to bottom:

- **The Daily Alignment Brief**, the one dark card, is a short AI-written summary with up to five suggested actions that link to candidates. It is generated once per company per day and cached; if the AI call fails, the card is simply absent.
- **Four figures:** open roles, active candidates (everyone not yet hired or rejected), people currently in interview, and pending actions.
- **Attention needed**, three lists that link straight to the work: applications waiting for review (Applied or Screening, oldest first), open jobs with fewer than five applicants, and draft emails awaiting review.
- **The hiring pipeline**, a funnel of how many applications sit at each stage.
- **Recent activity**, a time-sorted merge of recent resume analyses and hire-workflow runs in plain language.

Every list is capped at ten items, and everything except the brief is recalculated on each load.

### Jobs

The jobs screen has tabs for **Open** (the default), **Draft**, **Closed** and **All**, plus a title search. **New job** (admin and recruiter only; hidden from hiring managers) asks for title, description, employment type (full-time, part-time, contract, internship), location, an optional salary range with a currency (USD, EUR, GBP, CAD, a label only, with no conversion anywhere), and the three **scoring criteria**: required skills, preferred skills (both comma-separated) and the minimum years of experience. These three fields are what candidates are scored against, so the form explains that and says leaving the years blank skips that dimension.

A job starts as a **draft** and moves forward one step at a time: Draft, Open, Closed, Archived. Only open jobs appear on the public board and accept applications. Only a draft can be deleted, and deleting asks for a second confirming click.

**Limitation:** the backend can edit a job (`PATCH /jobs/{id}`), but **there is no edit screen**. A job's title, description and scoring criteria cannot be changed from the UI after creation. Because the criteria drive the score, this matters.

### Pipeline

The pipeline is a Kanban board with one column per stage, filterable by job. It is not drag-and-drop, because the rules only allow moving a candidate one step forward (or rejecting). Each card has **Advance** and **Reject** buttons for its one legal next move, and shows the candidate, the job, the alignment score and how long ago they applied.

### The candidate workspace

Opening a card opens the workspace for that application. The main column holds what you read and write; a right-hand rail holds what you act with.

**The assessment (Resume Intelligence)** shows, from the stored analysis and nothing computed in the browser: a large **alignment score** with its three **dimension bars** (required skills, preferred skills, experience, each a percentage, or "N/A" if that dimension was not scored); a short written **explanation**; the **required** and **preferred** skills each with a state (matched, not matched, or insufficient evidence) and the supporting quote from the resume; an **experience fit** card ("Meets minimum", "Below minimum" or "Minimum unknown") with its justification; **strengths** and **potential concerns**; and the analysis time. A **Re-analyze** button runs a fresh analysis (recruiter and admin only). If the review is still running it shows progress; if it failed it says so and offers **Try again**; if the candidate has no resume it says there is nothing to analyze yet.

**Communication** lets a recruiter draft an **interview invitation** or a **rejection** with one click. Each draft appears as an editable card (subject and body) with **Regenerate** and **Mark as sent**. Nothing is ever emailed: marking as sent records that the recruiter sent it through their own email, and the card says so. A sent email becomes read-only. Drafting is disabled once an application is Hired or Rejected, so **a rejection email has to be drafted before you reject the candidate**.

**The right rail** has the **pipeline** (the stage journey plus the buttons to move forward or reject; rejecting takes a confirmation click, while moving to Hired does not), **Ask Compass** (with suggested questions: "Why this score?", "What are this candidate's biggest gaps?", "Which required skills are missing?"), the **hire workflow** panel (appears once hired, section 7), and an **activity** feed built from real timestamps (application received, resume analysed with score, emails drafted and sent, hire workflow outcome).

**Known defect:** on a hired candidate, the **Regenerate** button of the welcome-email draft answers with an error (HTTP 500). Editing and marking that draft as sent work. See document 11.

### Knowledge Center

Admins can **upload** company documents (PDF, DOCX or TXT, up to 20 MB) with a title and a category (policy, benefits, procedure, other), **delete** them (with a confirming click) and **re-index** them. Each document shows its processing status as it moves from uploaded to ready, polling until it settles, with an error message if processing failed. Everyone who can open the page sees the library and the **Compass question box**, whose suggested questions are built from the real titles in the library. If no document is ready yet, the page says Compass is not ready instead of offering a box that cannot answer.

Compass's answers come only from this company's documents, cite the exact passages used, and carry a confidence level. When nothing relevant is found it says so plainly and suggests contacting HR or uploading the document.

### Leave approvals (admin and hiring manager)

The **Leave requests** page is a queue of pending requests across the company, with **Approve** (one click) and **Reject** (inline confirmation). A request that would push an employee past their allotment can still be approved, and the balance then shows a negative number rather than hiding it.

---

## 5. Hiring managers

A hiring manager sees the dashboard, jobs, the pipeline, every candidate workspace (including analyses and email history), the Knowledge Center and the leave-approval queue, and can approve or reject leave. They **cannot change anything in the hiring pipeline**: they cannot create jobs, move candidates, draft emails or re-run an analysis.

One thing to know about the interface: apart from "New job" and the knowledge-management controls, the buttons for those actions are **still visible** to a hiring manager. Pressing one shows the server's refusal ("You do not have permission to perform this action.", HTTP 403), as confirmed on the running backend. The server is always the real gatekeeper; the UI simply does not hide every control yet.

---

## 6. Employees

A person becomes an employee when a candidate is hired (section 7). An employee's experience is deliberately small:

- **A home page** that offers two shortcuts: request leave, and company knowledge.
- **My leave:** a balance card (days used against the annual allotment), a form to request time off (start date, end date, type, optional reason), and the list of their own requests with the option to **cancel** a pending one. The server refuses an end date before the start date and refuses a request that overlaps a pending or approved one.
- **Knowledge Center and Compass,** read-only: they can ask Compass company-policy questions from anywhere in the app with ⌘K.

The leave allowance is a single fixed number, **20 calendar days a year** for every employee of every company, counting calendar days inclusive of both ends. It is not configurable and is separate from whatever a company's own policy document says. (The seeded Helix Health policy document says 25, but its employees' balance would still show 20.)

An employee **cannot see anything about recruiting**, and an employee account created directly by an admin through the API, rather than through a hire, can sign in and read knowledge but cannot use leave (it has no employee record).

---

## 7. The hire workflow, as a user sees it

The moment a recruiter moves an application to **Hired**, Talign starts a four-step background process, and the candidate workspace shows it as a small checklist that refreshes until the result is in:

1. An **employee record** is created (name, email, job title, hire date).
2. An **onboarding checklist** of four fixed tasks is created: set up workstation, IT account provisioning, manager intro meeting, complete new-hire paperwork.
3. A **welcome email is drafted**, never sent, for the recruiter to review.
4. The candidate's login is **converted into an employee account** of the company.

The outcome is recorded as success, failed (naming the step that failed) or skipped (everything already existed, so nothing was done). Running it twice creates no duplicates. In this version the onboarding checklist is created and stored but there is **no screen on which an employee or HR can tick tasks off**.

---

## 8. Compass, everywhere

Compass is not a page; it is a panel opened with ⌘K (or Ctrl+K) from any protected page, plus the "Ask Compass" boxes embedded in the candidate workspace, the Knowledge Center and the leave page. What it can answer depends on who you are and where you are:

| Who and where | What Compass can answer |
| --- | --- |
| Candidate, on their own application | The current stage of that application, nothing else |
| Employee, anywhere | Company-policy questions from the company's documents |
| Admin/recruiter/hiring manager, on a candidate's page | That candidate's stored analysis ("Why this score?"), plus company policy |
| Admin/recruiter/hiring manager, anywhere else | Company-policy questions |

A user for whom there is nothing Compass could honestly answer is not offered the panel at all. The panel only decides what to *offer*; the server decides what is *allowed*.

---

## 9. Capabilities in the Product Book that are not in this version

These were part of the original vision and are intentionally not built: an Analytics screen, a notification centre, interview scheduling and interview kits, side-by-side candidate comparison (the "Decision Workspace"), real email sending, rediscovering past candidates, a separate AI activity log, ⌘K as a command palette that performs actions (it only asks questions), team invitations by email, password reset, and per-role dashboards for hiring managers beyond the shared one. Document 11 lists them with the reasoning.
