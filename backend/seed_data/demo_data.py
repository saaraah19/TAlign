"""
The demo world: three fictional companies, the people who work there, the
jobs they post, the candidates who apply, and what happens to each
application. Read by scripts/seed_demo.py, which plays it into a running
Talign backend through the public HTTP API.

The accounts mirror the personas in the Product Book: Emma the recruiter,
David the hiring manager, Olivia the HR director (admin), Alex the candidate
and Sarah the employee (a candidate who gets hired, so you can watch a
candidate turn into an employee).

Everything uses ONE demo password. These are throwaway accounts for a local
database; never seed a real deployment with them.
"""

DEMO_PASSWORD = "Demo!Pass123"

# ------------------------------------------------------------------ companies
COMPANIES = [
    {
        "key": "northwind",
        "name": "Northwind Robotics",
        "admin": {"first": "Olivia", "last": "Brown", "email": "olivia.brown@northwind-robotics.com"},
        "staff": [
            {"first": "Emma", "last": "Martin", "email": "emma.martin@northwind-robotics.com", "role": "recruiter"},
            {"first": "David", "last": "Chen", "email": "david.chen@northwind-robotics.com", "role": "hiring_manager"},
        ],
        "knowledge": [
            {"file": "northwind_employee_handbook.docx", "title": "Employee Handbook", "category": "policy"},
            {"file": "northwind_leave_policy.pdf", "title": "Leave Policy", "category": "policy"},
            {"file": "northwind_remote_work_policy.docx", "title": "Remote Work Policy", "category": "policy"},
            {"file": "northwind_benefits_guide.pdf", "title": "Benefits Guide", "category": "benefits"},
            {"file": "northwind_it_security_policy.txt", "title": "IT Security Policy", "category": "procedure"},
            {"file": "northwind_expense_procedure.pdf", "title": "Expense Reimbursement Procedure", "category": "procedure"},
        ],
        "jobs": [
            {
                "key": "backend",
                "title": "Backend Engineer",
                "final_status": "open",
                "employment_type": "full_time",
                "location": "Rotterdam / Hybrid",
                "salary_min": 60000, "salary_max": 85000, "salary_currency": "EUR",
                "required_skills": ["Python", "SQL", "REST APIs", "Docker", "PostgreSQL"],
                "preferred_skills": ["AWS", "Kubernetes"],
                "min_years_experience": 3,
                "description": (
                    "Join the platform team that powers our fleet of warehouse robots. You will design and build the "
                    "REST APIs our robots and dashboards depend on, own the PostgreSQL data model, and ship services "
                    "in containers.\n\nYou will work with product, firmware and operations teams, review code, and "
                    "help us keep the platform fast and reliable."
                ),
            },
            {
                "key": "ml",
                "title": "Machine Learning Engineer",
                "final_status": "open",
                "employment_type": "full_time",
                "location": "Remote (Europe)",
                "salary_min": 70000, "salary_max": 95000, "salary_currency": "EUR",
                "required_skills": ["Python", "PyTorch", "Machine Learning", "SQL"],
                "preferred_skills": ["MLOps", "AWS"],
                "min_years_experience": 3,
                "description": (
                    "Build the perception models that let our robots see and handle packages. You will train and "
                    "evaluate models, take them to production, and work closely with the robotics team on real-world "
                    "performance."
                ),
            },
            {
                "key": "frontend",
                "title": "Frontend Engineer",
                "final_status": "open",
                "employment_type": "full_time",
                "location": "Remote",
                "salary_min": 55000, "salary_max": 78000, "salary_currency": "EUR",
                "required_skills": ["TypeScript", "React", "CSS", "REST APIs"],
                "preferred_skills": ["Next.js", "accessibility"],
                "min_years_experience": 2,
                "description": (
                    "Create the control-room interfaces operators use to supervise robots in real time. We care about "
                    "clarity, speed and accessibility."
                ),
            },
            {
                "key": "devops",
                "title": "DevOps Engineer",
                "final_status": "open",
                "employment_type": "contract",
                "location": "Rotterdam",
                "salary_min": 450, "salary_max": 600, "salary_currency": "EUR",
                "required_skills": ["Docker", "Kubernetes", "CI/CD", "AWS", "Linux"],
                "preferred_skills": ["Terraform", "Python"],
                "min_years_experience": 4,
                "description": (
                    "A 12-month contract (day rate) to strengthen our cloud platform: Kubernetes clusters, delivery "
                    "pipelines and observability."
                ),
            },
            {
                "key": "designer",
                "title": "Product Designer",
                "final_status": "draft",
                "employment_type": "full_time",
                "location": "Rotterdam / Hybrid",
                "salary_min": None, "salary_max": None, "salary_currency": "EUR",
                "required_skills": ["Figma", "UX research", "Design systems"],
                "preferred_skills": ["Prototyping"],
                "min_years_experience": 3,
                "description": "A draft role we are still shaping: not yet published, so candidates cannot see or apply to it.",
            },
            {
                "key": "support",
                "title": "Customer Success Manager",
                "final_status": "closed",
                "employment_type": "full_time",
                "location": "Rotterdam",
                "salary_min": 48000, "salary_max": 62000, "salary_currency": "EUR",
                "required_skills": ["Customer support", "CRM", "Communication"],
                "preferred_skills": [],
                "min_years_experience": 2,
                "description": "A role we have already filled: closed, so it no longer accepts applications.",
            },
        ],
    },
    {
        "key": "helix",
        "name": "Helix Health",
        "admin": {"first": "Grace", "last": "Okafor", "email": "grace.okafor@helix-health.io"},
        "staff": [
            {"first": "Liam", "last": "Becker", "email": "liam.becker@helix-health.io", "role": "recruiter"},
        ],
        "knowledge": [
            {"file": "helix_privacy_handbook.pdf", "title": "Patient Data Privacy Handbook", "category": "policy"},
            {"file": "helix_leave_policy.txt", "title": "Leave Policy", "category": "policy"},
        ],
        "jobs": [
            {
                "key": "analyst",
                "title": "Healthcare Data Analyst",
                "final_status": "open",
                "employment_type": "full_time",
                "location": "Milan / Hybrid",
                "salary_min": 42000, "salary_max": 58000, "salary_currency": "EUR",
                "required_skills": ["SQL", "Python", "Tableau"],
                "preferred_skills": ["healthcare data"],
                "min_years_experience": 2,
                "description": "Turn hospital data into decisions for clinicians, with privacy built in from the start.",
            },
            {
                "key": "pm",
                "title": "Clinical Product Manager",
                "final_status": "open",
                "employment_type": "full_time",
                "location": "Remote (EU)",
                "salary_min": 70000, "salary_max": 95000, "salary_currency": "EUR",
                "required_skills": ["Product management", "healthcare", "stakeholder management"],
                "preferred_skills": ["analytics"],
                "min_years_experience": 5,
                "description": "Lead product discovery and delivery for tools used by clinicians every day.",
            },
        ],
    },
    {
        # A brand-new company with nothing in it: the quickest way to see every empty state.
        "key": "brightpath",
        "name": "Brightpath Logistics",
        "admin": {"first": "Noah", "last": "Fischer", "email": "noah.fischer@brightpath-logistics.com"},
        "staff": [],
        "knowledge": [],
        "jobs": [],
    },
]

# ----------------------------------------------------------------- candidates
# `applications`: (company key, job key) pairs. `resume` is the file in
# seed_data/resumes/. `extra_resumes` are uploaded but not used to apply.
CANDIDATES = [
    {"first": "Alex", "last": "Johnson", "email": "alex.johnson@candidates-demo.com", "resume": "alex_johnson.pdf",
     "applications": [("northwind", "backend")]},
    {"first": "Priya", "last": "Nair", "email": "priya.nair@candidates-demo.com", "resume": "priya_nair.pdf",
     "applications": [("northwind", "backend")]},
    {"first": "Sarah", "last": "Lopez", "email": "sarah.lopez@candidates-demo.com", "resume": "sarah_lopez.docx",
     "applications": [("northwind", "backend")]},
    {"first": "Fatima", "last": "Zahra", "email": "fatima.zahra@candidates-demo.com", "resume": "fatima_zahra.pdf",
     "applications": [("northwind", "backend")]},
    {"first": "Marcus", "last": "Webb", "email": "marcus.webb@candidates-demo.com", "resume": "marcus_webb.txt",
     "applications": [("northwind", "backend")]},
    {"first": "Chloé", "last": "Dubois", "email": "chloe.dubois@candidates-demo.com", "resume": "chloe_dubois.pdf",
     "applications": [("northwind", "backend")]},
    {"first": "James", "last": "O'Connor", "email": "james.oconnor@candidates-demo.com", "resume": "james_oconnor.pdf",
     "applications": [("northwind", "backend")]},
    {"first": "Daniel", "last": "Kim", "email": "daniel.kim@candidates-demo.com", "resume": "daniel_kim.pdf",
     "applications": [("northwind", "backend"), ("northwind", "devops")]},
    {"first": "Lina", "last": "Haddad", "email": "lina.haddad@candidates-demo.com", "resume": "lina_haddad.pdf",
     "applications": [("northwind", "frontend"), ("northwind", "backend")]},
    {"first": "Nadia", "last": "Petrova", "email": "nadia.petrova@candidates-demo.com", "resume": "nadia_petrova.docx",
     "applications": [("northwind", "frontend")]},
    {"first": "Hannah", "last": "Schmidt", "email": "hannah.schmidt@candidates-demo.com", "resume": "hannah_schmidt.pdf",
     "extra_resumes": ["hannah_schmidt_scanned.pdf"],
     "applications": [("northwind", "frontend")]},
    {"first": "Wei", "last": "Zhang", "email": "wei.zhang@candidates-demo.com", "resume": "wei_zhang.pdf",
     "applications": [("northwind", "ml")]},
    {"first": "Tomás", "last": "Rivera", "email": "tomas.rivera@candidates-demo.com", "resume": "tomas_rivera.pdf",
     "applications": [("northwind", "ml"), ("northwind", "backend")]},
    {"first": "Ahmed", "last": "Benali", "email": "ahmed.benali@candidates-demo.com", "resume": "ahmed_benali.pdf",
     "applications": [("northwind", "devops"), ("northwind", "backend")]},
    {"first": "Elena", "last": "Rossi", "email": "elena.rossi@candidates-demo.com", "resume": "elena_rossi.pdf",
     "applications": [("helix", "analyst")]},
    {"first": "Omar", "last": "Khalil", "email": "omar.khalil@candidates-demo.com", "resume": "omar_khalil.txt",
     "applications": [("helix", "pm")]},
]

# ------------------------------------------------------ what recruiters then do
# `moves`: the stages to advance through, in order (rejection ends the story).
# `draft`: an email to draft for that application; `mark_sent` records that the
# recruiter sent it. Applications not listed stay at "applied".
PIPELINE = [
    {"company": "northwind", "job": "backend", "candidate": "alex.johnson@candidates-demo.com",
     "moves": ["screening", "interview"], "draft": "interview_invitation", "mark_sent": False},
    {"company": "northwind", "job": "backend", "candidate": "priya.nair@candidates-demo.com",
     "moves": ["screening"]},
    {"company": "northwind", "job": "backend", "candidate": "fatima.zahra@candidates-demo.com",
     "moves": ["rejected"], "draft": "rejection", "mark_sent": True},
    {"company": "northwind", "job": "backend", "candidate": "sarah.lopez@candidates-demo.com",
     "moves": ["screening", "interview", "offer", "hired"]},   # becomes an employee
    {"company": "northwind", "job": "ml", "candidate": "wei.zhang@candidates-demo.com",
     "moves": ["screening", "interview", "offer"]},
    {"company": "northwind", "job": "ml", "candidate": "tomas.rivera@candidates-demo.com",
     "moves": ["screening"]},
    {"company": "northwind", "job": "devops", "candidate": "ahmed.benali@candidates-demo.com",
     "moves": ["screening", "interview"]},
    {"company": "helix", "job": "analyst", "candidate": "elena.rossi@candidates-demo.com",
     "moves": ["screening"]},
]

# ------------------------------------------------- leave requests (after hiring)
# Sarah Lopez, once hired, is an employee. Days are offsets from "today".
LEAVE = {
    "employee": "sarah.lopez@candidates-demo.com",
    "company": "northwind",
    "requests": [
        {"type": "vacation", "start_in_days": 45, "length_days": 5, "reason": "Family trip", "outcome": "pending"},
        {"type": "sick", "start_in_days": 10, "length_days": 2, "reason": "Dentist and recovery", "outcome": "approve", "by": "david.chen@northwind-robotics.com"},
        {"type": "personal", "start_in_days": 20, "length_days": 1, "reason": "Moving day", "outcome": "reject", "by": "olivia.brown@northwind-robotics.com"},
    ],
}

# Where each recruiter sees each job's applicants, for the closing summary.
RECRUITER_FOR = {"northwind": "emma.martin@northwind-robotics.com", "helix": "liam.becker@helix-health.io"}
