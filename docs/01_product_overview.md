# 01 — Product overview

This document explains what Talign is for, who it serves, the principles it was designed around, and how much of the original vision is built. It is the "why" that the rest of the documentation builds on. For the "what is on each screen" see document 03; for the honest list of what is missing see document 11.

---

## 1. What Talign is, and what it is not

Talign is an AI-native talent operating system. The phrase "operating system" is deliberate: it is meant to hold the whole life of a person's relationship with a company, from the first time they look at a job, through hiring and onboarding, to the everyday questions of working there, in one product, with one identity, and one AI assistant.

It is **not an applicant-tracking system (ATS)**, which is a database of candidates with a pipeline on top. Many such tools have since added an AI button. Talign inverts that: the working assumption is that the AI is present in every interaction, and the product is organised around that, rather than around a form with an AI feature attached.

It is **not a chatbot**. The AI is not a destination page that you open to talk to. It is a presence inside the screens you already work in, aware of where you are and who you are, which is why its answers adapt to a recruiter looking at one candidate, an employee asking about leave, or a candidate wondering what stage they are at.

The original brief summarised it in one line: *Talign isn't an HR platform with AI. It's an AI platform specialized in HR.*

---

## 2. The problem

The product began from a plain observation about a recruiter's day: she spends more time *managing* recruitment than *recruiting*. She reads hundreds of resumes with no principled place to start, writes the same emails every day, waits for hiring managers who are busy, searches five tools for one fact, answers employees' repeated questions by email, and ends the day with dozens of unread messages and the sense that something was forgotten. Each person around her has the mirror-image problem: managers have no time and no summary; employees can't find a document and wait days for HR; candidates hear nothing; and the HR director can't see any of it.

Every feature in Talign was meant to answer a measurable version of one of these problems, and a feature that did not was meant to be left out.

---

## 3. Who it is for

The design started from five people. Their own words, and what the built product gives each of them, are below. The right-hand column is deliberately candid about what is not built.

| Person | In their words | What Talign gives them today | What is not built |
| --- | --- | --- | --- |
| **Emma Martin**, recruiter | "I spend more time managing recruitment than actually recruiting." | A dashboard of what needs attention, resumes scored and *explained*, drafted emails to review, a pipeline | Interview scheduling; a view of her whole workload over time |
| **David Chen**, hiring manager | "I don't recruit people. I build teams." | Read access to the whole pipeline and every analysis, so he can judge a candidate from a summary instead of a long resume; leave approvals | His own dedicated dashboard; interview kits; approving a hire directly (his access to the pipeline is read-only) |
| **Sarah Lopez**, employee | "I shouldn't have to contact HR for every simple question." | Company-policy answers with the cited document, a leave balance, requesting and tracking leave | Documents and certificates to download; completing onboarding tasks |
| **Alex Johnson**, candidate | "I just want to know what's happening with my application." | The stage of every application, the progress of the automated review, one-click applying | Interview scheduling; AI interview preparation; accepting an offer in the product |
| **Olivia Brown**, HR director | "I need visibility, not more spreadsheets." | The shared dashboard and the daily brief; an admin role over everything | Analytics, KPIs over time, recruiter productivity, exports |

The honest summary is that the **recruiter and the candidate-to-employee journey are built in depth**, and the HR director's analytics are the largest piece of the vision that is not.

---

## 4. The principles, and how the build honours them

The Product Book set six principles to guide every decision. Here is each one, and what it turned into.

**AI assists, humans decide.** The most strictly applied of the six. No agent can hire, reject or send anything; stage changes are human actions behind role checks; the hire workflow is triggered only by a person; emails are drafts a person marks as sent; and the AI never produces a number, because scores and counts are computed by ordinary code.

**Explain every important decision.** Every score shows the evidence for each skill, the three dimension percentages and a written explanation; every policy answer cites the passage it came from; confidence is computed from retrieval strength, never self-reported by the model; and every analysis records which model, prompt and scoring version produced it.

**One source of truth.** Partly met. Company policy, people, jobs, applications, resumes and leave all live in one place, and the Knowledge Center is the single store Compass answers from. But Talign does not integrate with the tools the original problem lists (calendars, spreadsheets, mail), so "everything findable from Talign" holds for what Talign holds, not for what lives elsewhere.

**Reduce clicks, not control.** Applying is one page and one click; opening a candidate shows the assessment, the email draft and the pipeline together; but a rejection still asks for a second confirmation, and a sent email can never be edited, so convenience stops where control begins.

**Every screen answers one question.** The dashboard answers "what should I do today?", the pipeline "who is where?", the candidate workspace "should I move forward with this person?", the Knowledge Center "can you help me?". It is a design discipline more than a checkable property, and it is why screens are kept deliberately small.

**Automation should feel invisible.** The user never chooses an agent: they ask Compass, and a router picks the capability. The hire workflow and the resume analysis run in the background and the screen simply updates. The cost of invisibility is that you must be able to look inside when you need to, which is why results carry their provenance.

---

## 5. The ideas the product is built around

**Compass is a presence, not a page.** There is no "Compass" screen to navigate to. It appears in the places where a question naturally arises, and opens anywhere with ⌘K (or Ctrl+K). What it can answer depends on who is asking and where, and that adaptation is enforced by the server, not just hidden in the interface.

**Objects have workspaces.** Opening a candidate does not open a record; it opens a workspace that gathers their assessment, their emails, their stage and an assistant that already knows the context. When you ask "why this score?" you never say whose.

**One identity, two chapters.** The person who applies is the person who, once hired, is an employee. Hiring converts their account in place. This is the clearest case of the product's data model expressing its philosophy: there is one table of people, and roles say what each may do.

**Progressive disclosure.** The product tries to look almost too simple, with power available on demand: a short form to create a job, an optional scoring checklist, advanced detail behind a click.

---

## 6. How much of the vision is built

The MVP rule was that ten polished features beat fifty unfinished ones, and that anything outside the MVP must be explained and left out rather than silently added. The built product covers: accounts and roles; jobs and a public job board; applications and a pipeline; Resume Intelligence; email drafting; the Knowledge Center with grounded answers; the dashboard with a daily brief; the hire workflow; the employee experience with leave and approvals; and Compass.

Left out on purpose are analytics, notifications, interview scheduling and kits, candidate comparison, rediscovery of past candidates, real email sending, and a command palette that performs actions. The reasoning for each is in document 11, along with the defects and rough edges that are known.

---

## 7. How it was built

Talign was built in **vertical slices**: each slice delivered a thin but complete piece of the product, with the database, backend, API, frontend and documentation together, so that at every point there was a working, demonstrable product rather than a half-built layer. Engineering conventions were fixed early and applied throughout: two-layer validation (a database constraint *and* a service check) for every rule that matters; state machines kept private to the service that owns them; domain events as a vocabulary rather than an event bus; agents receiving plain data and never a database session; and architectural boundaries enforced by tests rather than by good intentions. The design notes for the first slices are kept in `docs/history/`.
