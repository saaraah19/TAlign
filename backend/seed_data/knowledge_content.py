# ruff: noqa: ISC004  (long paragraphs are written as adjacent string literals on purpose, for readability)
"""
Text of the demo company documents that the Knowledge Agent answers from.
Rendered by build_assets.py to PDF / DOCX / TXT under seed_data/knowledge/.

Every document states concrete, checkable facts (numbers, deadlines, names
of systems) so that a Compass answer can be verified against the source.
Helix Health's leave policy deliberately differs from Northwind Robotics'
(25 vs 20 days): asking each company's employees "how many leave days do I
get?" proves that companies cannot see each other's documents.
"""

DOCUMENTS = {
    # ============================================================ Northwind Robotics
    "northwind_employee_handbook": {
        "format": "docx",
        "title": "Northwind Employee Handbook",
        "sections": [
            ("Welcome to Northwind Robotics", [
                "Northwind Robotics builds autonomous warehouse robots. We are about 300 people across "
                "engineering, operations, sales and people teams, working from our Rotterdam headquarters and remotely.",
                "This handbook explains how we work together. If something here is unclear, ask People & Culture "
                "through Talign or write to people@northwind-robotics.com.",
            ]),
            ("Working hours", [
                "The standard working week is 38 hours. Our core hours, when everyone is expected to be reachable, "
                "are 10:00 to 15:00 Central European Time, Monday to Friday.",
                "Outside core hours you are free to organise your day, as long as your team's commitments are met.",
            ]),
            ("Code of conduct", [
                "We treat colleagues, candidates and partners with respect. Harassment and discrimination of any kind "
                "are not tolerated and are grounds for dismissal.",
                "Concerns can be raised confidentially with People & Culture or through the anonymous Speak-Up form "
                "on the intranet. Retaliation against anyone who raises a concern in good faith is prohibited.",
            ]),
            ("Probation and reviews", [
                "New employees have a probation period of 3 months, with a check-in at 6 weeks and a final review at the end.",
                "Everyone has a development review twice a year, in April and October.",
            ]),
            ("Who to contact", [
                "Leave and payroll questions: People & Culture. Equipment and accounts: the IT Service Desk. "
                "Expenses: Finance. You can also ask Compass in Talign, which answers from the company documents.",
            ]),
        ],
    },
    "northwind_leave_policy": {
        "format": "pdf",
        "title": "Northwind Leave Policy",
        "sections": [
            ("Annual leave", [
                "Every full-time employee receives 20 days of paid annual leave per calendar year, in addition to public holidays.",
                "Leave is counted in calendar days between the start and end date of the request, both included.",
            ]),
            ("How to request leave", [
                "Submit a leave request in Talign, under Leave. State the type (vacation, sick or personal), the dates and an optional reason.",
                "A request is reviewed by an administrator or a hiring manager. Please submit vacation requests at least 2 weeks in advance.",
                "You can cancel a request while it is still pending.",
            ]),
            ("Sick leave", [
                "If you are unwell, tell your team on the first morning and submit a sick leave request in Talign as soon as you can.",
                "A medical certificate is required from the 4th consecutive day of sick leave.",
            ]),
            ("Carry-over", [
                "Up to 5 unused leave days can be carried over into the next year and must be taken before 31 March.",
                "Any other unused days expire on 31 December.",
            ]),
            ("Parental leave", [
                "Primary caregivers receive 16 weeks of paid parental leave; secondary caregivers receive 6 weeks. See the Benefits Guide for details.",
            ]),
        ],
    },
    "northwind_remote_work_policy": {
        "format": "docx",
        "title": "Northwind Remote Work Policy",
        "sections": [
            ("Our hybrid model", [
                "Northwind works hybrid. Employees are expected in the Rotterdam office on 2 days per week, and may work remotely on the others.",
                "Teams agree their anchor days together, so that colleagues overlap in the office.",
            ]),
            ("Working from abroad", [
                "You may work remotely from another country for up to 20 working days per year, with your manager's approval, "
                "because tax and social-security rules can apply beyond that. Request it at least 4 weeks ahead.",
            ]),
            ("Equipment and home office", [
                "Northwind provides a laptop, and a one-time home-office budget of 400 euros for a desk, chair or monitor. "
                "Receipts are reimbursed through the expense process.",
                "Internet costs are covered with a monthly allowance of 30 euros for remote-working employees.",
            ]),
            ("Security when remote", [
                "Use the company VPN on public networks and never work on company data from shared computers. See the IT Security Policy.",
            ]),
        ],
    },
    "northwind_benefits_guide": {
        "format": "pdf",
        "title": "Northwind Benefits Guide",
        "sections": [
            ("Health and wellbeing", [
                "Northwind pays 100% of the basic health-insurance premium for employees and 50% for their dependants.",
                "Every employee has access to a confidential employee-assistance programme, with up to 6 free counselling sessions per year.",
            ]),
            ("Pension", [
                "Northwind contributes 6% of gross salary to the company pension scheme; employees may add voluntary contributions.",
            ]),
            ("Learning budget", [
                "Each employee has a learning budget of 1,200 euros per year for courses, books and conferences, approved by their manager.",
            ]),
            ("Parental leave", [
                "Primary caregivers receive 16 weeks of fully paid parental leave and secondary caregivers 6 weeks. "
                "Leave can be taken any time within the first 12 months after the birth or adoption.",
            ]),
            ("Mobility", [
                "A public-transport pass or a bicycle lease is available. Employees who commute by bicycle receive 0.25 euros per kilometre.",
            ]),
        ],
    },
    "northwind_it_security_policy": {
        "format": "txt",
        "title": "Northwind IT Security Policy",
        "sections": [
            ("Passwords and multi-factor authentication", [
                "Passwords must be at least 14 characters and must never be reused across systems. Use the company password manager.",
                "Multi-factor authentication is mandatory for email, the code repository and the cloud console.",
            ]),
            ("Devices", [
                "Company laptops must have disk encryption and automatic updates enabled. Lock your screen whenever you step away.",
                "Personal devices may only access company email, and only through the managed mail application.",
            ]),
            ("Reporting an incident", [
                "If you lose a device, click a suspicious link or suspect an account has been compromised, report it immediately to "
                "security@northwind-robotics.com or the IT Service Desk, at any time of day. Reporting quickly is never penalised.",
            ]),
            ("Customer and employee data", [
                "Confidential data must only be stored on approved company systems. Never send it to personal email or consumer file-sharing tools.",
            ]),
        ],
    },
    "northwind_expense_procedure": {
        "format": "pdf",
        "title": "Northwind Expense Reimbursement Procedure",
        "sections": [
            ("What can be claimed", [
                "Business travel, client meals, approved equipment and training are reimbursable. Personal items and alcohol are not.",
                "Meals while travelling are reimbursed up to 35 euros per day.",
            ]),
            ("How to claim", [
                "Submit your expense report within 30 days of the expense, with the original receipt, through the Finance portal.",
                "Your manager approves the report; Finance then pays it in the next monthly payroll run.",
            ]),
            ("Approval limits", [
                "Single expenses above 500 euros need your manager's approval before you spend. Above 2,500 euros they need Finance approval too.",
            ]),
        ],
    },
    # ============================================================ Helix Health
    "helix_privacy_handbook": {
        "format": "pdf",
        "title": "Helix Health Patient Data Privacy Handbook",
        "sections": [
            ("Why it matters", [
                "Helix Health handles sensitive patient data. Protecting it is a legal duty and the foundation of our patients' trust.",
            ]),
            ("Access rules", [
                "Access patient records only when you need them for your role (the minimum-necessary rule). Every access is logged and reviewed monthly.",
            ]),
            ("Breaches", [
                "Report any suspected breach to the Data Protection Officer within 24 hours. The company must notify the regulator within 72 hours.",
            ]),
        ],
    },
    "helix_leave_policy": {
        "format": "txt",
        "title": "Helix Health Leave Policy",
        "sections": [
            ("Annual leave", [
                "Every full-time Helix Health employee receives 25 days of paid annual leave per year, plus public holidays.",
            ]),
            ("Requests", [
                "Request leave through the HR portal at least 3 weeks in advance for stays longer than 5 days.",
            ]),
        ],
    },
}
