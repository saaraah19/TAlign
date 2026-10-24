# 10 — Try it in 10 minutes

Talign comes with a demo world: three companies, sixteen candidates with real resume files, eight company documents, twenty applications at different stages, and one person who has already been hired and become an employee. This guide loads it, then walks you through it in about ten minutes, stop by stop, telling you what to click and what you should see.

The demo world is not a mock-up. A script plays it through the application's own public API, exactly as a browser would, so what you explore is the real product with real data in a real database.

---

## 1. Load the demo world

Start the stack and create the tables (see document 09 for details), then run the seed script:

```bash
docker compose up --build
docker compose exec backend alembic upgrade head          # first run only
docker compose exec backend python scripts/seed_demo.py
```

**Use a real `GOOGLE_API_KEY` in your `.env`.** The seed asks the AI to analyse resumes, draft emails and embed documents. Without a key, the script still creates every account, job, application and document, and tells you which AI steps failed, but you will not see scores, drafts or Compass answers. With a key, the script waits for the background analyses to finish (a few minutes).

The script is safe to run again: each step checks whether its work already exists, so a second run creates nothing new. To wipe the world and start over, run `docker compose down -v` (this deletes the database and uploaded files) and repeat the commands above.

### Who you can sign in as

Every account uses the same password: **`Demo!Pass123`**. The email addresses use made-up domains.

| Person | Email | Role | Company |
| --- | --- | --- | --- |
| Olivia Brown | `olivia.brown@northwind-robotics.com` | Admin | Northwind Robotics |
| Emma Martin | `emma.martin@northwind-robotics.com` | Recruiter | Northwind Robotics |
| David Chen | `david.chen@northwind-robotics.com` | Hiring manager | Northwind Robotics |
| Grace Okafor | `grace.okafor@helix-health.io` | Admin | Helix Health |
| Liam Becker | `liam.becker@helix-health.io` | Recruiter | Helix Health |
| Noah Fischer | `noah.fischer@brightpath-logistics.com` | Admin | Brightpath Logistics (empty on purpose) |
| Sarah Lopez | `sarah.lopez@candidates-demo.com` | **Employee** (hired) | Northwind Robotics |
| Alex Johnson | `alex.johnson@candidates-demo.com` | Candidate (at the interview stage) | none |
| Wei Zhang | `wei.zhang@candidates-demo.com` | Candidate (holding an offer) | none |

The other candidates follow the pattern `first.last@candidates-demo.com`: Priya Nair, Fatima Zahra, Marcus Webb, Chloé Dubois, James O'Connor, Daniel Kim, Lina Haddad, Nadia Petrova, Hannah Schmidt, Tomás Rivera, Ahmed Benali (Northwind jobs) and Elena Rossi and Omar Khalil (Helix jobs).

Use two browser windows (or one normal and one private window) so you can be signed in as two people at once.

---

## 2. The tour

### Stop 1 — The public job board (1 minute, no sign-in)

Open <http://localhost:3000/careers>. You see the **six open jobs** on the platform: four at Northwind Robotics (Backend, Machine Learning, Frontend and DevOps engineers) and two at Helix Health. Each card shows the employer, the location, the salary range and the required skills. The product designer role and the customer-success role at Northwind are not listed: one is a draft and one is closed, and only open jobs are public. Open any job to see the full description and its **Apply** button.

### Stop 2 — The recruiter's morning (2 minutes)

Sign in as **Emma Martin** (the recruiter). The **Dashboard** shows what needs attention today. With the demo data you should see **4 open jobs, 16 active candidates, 2 people in interview**, and the hiring funnel: **11 applied, 2 in screening, 2 in interview, 1 with an offer, 1 hired, 1 rejected** (18 applications at Northwind). The dark card at the top is the **Daily Alignment Brief**, a short AI-written summary with suggested next actions. Below it are the lists that link to the work: applications waiting for review, open jobs with few applicants, and draft emails to review.

Open **Pipeline**. Each column is a stage, and each card shows the candidate, the job and the **alignment score**. Use the filter to look at one job at a time.

### Stop 3 — Understand one candidate (3 minutes)

From the pipeline, open **Alex Johnson** (Backend Engineer, at the interview stage). This is the candidate workspace.

- **The assessment.** A large alignment score, three bars (required skills, preferred skills, experience), a written explanation, and each required and preferred skill marked *matched*, *not matched* or *insufficient evidence*, with the supporting quote from the resume. Read a few: this is the explainability the product is built around. The recruiter set the checklist (the job's required and preferred skills and minimum years); the AI only judges the resume against it, and the score is computed by ordinary code from those judgements.
- **Communication.** A drafted **interview invitation**, waiting for review. It is a draft: edit it, regenerate it, or mark it as sent. Talign never emails anyone.
- **Ask Compass.** Press the suggested question "Why this score?" The answer explains the stored analysis in a few sentences; it cannot change the score.

Now open **Fatima Zahra** (Backend Engineer, rejected). Her workspace shows a rejection email that was drafted **before** she was rejected and then marked as sent. The order matters: once a candidate is rejected the application is closed and new drafts are refused.

Two candidates are there to show the edges. **Hannah Schmidt** has a resume that is a scanned image, which the system could not read (it reports that clearly rather than guessing). **Daniel Kim**, **Lina Haddad**, **Tomás Rivera** and **Ahmed Benali** each applied to two jobs with **one** resume, which was uploaded once and reused.

### Stop 4 — Ask the company's documents (1 minute)

Open **Knowledge**. Northwind's six documents are listed, each marked ready. Use the question box (or press ⌘K / Ctrl+K from anywhere) and ask questions whose answers you can check against the documents. You should get an answer with the cited passage and a confidence level:

| Ask | You should find |
| --- | --- |
| How many days of annual leave do I get? | 20 days a year, counted in calendar days, both ends included |
| Can I work from another country? | Up to 20 working days a year, with the manager's approval, requested at least 4 weeks ahead |
| How much is the home-office budget? | A one-time 400 euros, plus 30 euros a month for internet |
| When do I need a medical certificate? | From the 4th consecutive day of sick leave |
| What do I get for meals while travelling? | Up to 35 euros a day |

Then ask something the documents do **not** cover, such as the dress code. The correct answer is a plain "I don't have information about that", with a suggestion to ask HR. An answer that invents a policy would be a defect.

### Stop 5 — The same person, two lives: hiring and becoming an employee (2 minutes)

This is the most distinctive thing in Talign. In the recruiter window, open **Wei Zhang** (Machine Learning Engineer, holding an offer) and move the application to **Hired**. Watch the **hire workflow** panel: it creates the employee record, creates the onboarding checklist, drafts a welcome email (a draft, never sent), and converts Wei's account into an employee account. This is a fixed four-step process, not an AI deciding things, and it is safe to run twice.

In the other window, sign in as **Wei Zhang** with the same email and password as before. The navigation has changed: it is now an employee's view (Dashboard, Knowledge, Leave), and the same person who applied minutes ago is a Northwind employee. There was never a second account.

(You can also sign in as **Sarah Lopez**, who was hired by the seed script, to see the same thing without waiting.) As Sarah, open **My leave**: the balance shows **2 of 20 days used**, one vacation request is **pending**, one sick-leave request is approved and one personal request was rejected.

### Stop 6 — Close the loop, and see the walls between companies (1 minute)

Sign in as **David Chen** (the hiring manager) and open **Leave requests**. Sarah's pending vacation request is in the queue: approve it, and her balance changes. Try something a hiring manager is not allowed to do, such as moving a candidate to the next stage: the server refuses it. David can read the whole pipeline but cannot change it.

Finally, sign in as **Grace Okafor** (Helix Health's admin). She sees only Helix's two jobs, two applications and two documents, and none of Northwind's data. Ask Compass the leave question: Helix's answer is **25 days**, not Northwind's 20, which proves each company's documents are separate. Sign in as **Noah Fischer** (Brightpath Logistics) for the quickest tour of every empty state, since that company has no data at all.

---

## 3. If you only have three minutes

Do Stop 3 for one candidate, then Stop 5 for the hiring and the sign-in as the same person. Those two show the explainable AI and the one-identity, two-lives idea, which are what make Talign different.

---

## 4. What is real and what to be careful about

- Everything you click is the real application on a real database. The demo script uses the public API only; it has no special access.
- The AI results (scores, explanations, drafts, the daily brief, Compass answers) come from the real model when you have a real key. The resumes were written to produce a spread: strong matches, partial matches, candidates below the experience minimum, and vague resumes that exercise "insufficient evidence". **The intended spread has not yet been seen on a real run**, so treat your first run as the first real look, and report anything that looks wrong.
- If you ran the seed *without* a key, scores and drafts are absent. The cleanest fix is to add the key, wipe the world (`docker compose down -v`) and seed again. The script does retry an analysis that fails during one run (for example a momentary rate limit), but it is not designed to repair a whole run made without a key.
- The password is published in this repository. Never load the demo world into a deployment that is reachable from the internet.
- A deliberate limit to expect: an employee account that an admin creates directly (rather than through a hire) has no employee record and cannot use leave. The seed avoids this by creating employees only through the hire path.
