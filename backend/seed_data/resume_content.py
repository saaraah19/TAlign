"""
Text of the demo candidates' resumes. `build_assets.py` renders each entry
to a PDF, DOCX or TXT file under seed_data/resumes/ (the rendered files are
committed, so you do not need to run the builder to use the demo data).

These are fictional people and employers. Each resume is written to produce
a specific, instructive outcome when scored against the demo jobs, noted in
the `purpose` field. Skills are named explicitly where a candidate truly has
them and are left out (or only hinted at) where they don't, because the
Resume Intelligence agent scores what the resume actually says.
"""

RESUMES = {
    # ---------------------------------------------------------------- strong backend
    "alex_johnson": {
        "format": "pdf",
        "purpose": "Strong backend match: every required skill, both preferred, 6 years.",
        "name": "Alex Johnson",
        "headline": "Senior Backend Engineer",
        "contact": "alex.johnson@candidates-demo.com · Lyon, France · linkedin.com/in/alex-johnson-demo",
        "summary": "Backend engineer with 6 years building high-traffic REST APIs in Python. "
        "Comfortable owning a service from design to production on AWS.",
        "experience": [
            ("Senior Backend Engineer", "Orbit Labs", "2022 – present", [
                "Lead a team of 4 maintaining a payments API (Python, FastAPI, PostgreSQL) serving 2M requests/day.",
                "Cut p95 latency by 40% by redesigning slow SQL queries and adding Redis caching.",
                "Containerised all services with Docker and deployed them on Kubernetes (EKS) on AWS.",
            ]),
            ("Backend Engineer", "Quantum Freight", "2019 – 2022", [
                "Built REST APIs in Python (Django REST Framework) for shipment tracking.",
                "Designed the PostgreSQL schema and wrote migrations; introduced CI with GitHub Actions.",
            ]),
        ],
        "skills": "Python, FastAPI, Django, REST APIs, SQL, PostgreSQL, Docker, Kubernetes, AWS (EC2, RDS, S3), Redis, CI/CD",
        "education": "BSc Computer Science, Université de Lyon, 2018",
    },
    "priya_nair": {
        "format": "pdf",
        "purpose": "Good backend match, but no AWS or Kubernetes (preferred skills missing).",
        "name": "Priya Nair",
        "headline": "Backend Engineer",
        "contact": "priya.nair@candidates-demo.com · Bangalore, India",
        "summary": "Backend engineer with 5 years of experience designing reliable APIs and data models.",
        "experience": [
            ("Backend Engineer", "Bluepeak Systems", "2021 – present", [
                "Develop REST APIs in Python (Flask, FastAPI) backed by PostgreSQL.",
                "Write complex SQL for reporting and own database performance tuning.",
                "Package services in Docker and automate builds with Jenkins.",
            ]),
            ("Software Engineer", "Meridian Software", "2019 – 2021", [
                "Maintained internal REST services in Python and MySQL.",
            ]),
        ],
        "skills": "Python, Flask, FastAPI, REST APIs, SQL, PostgreSQL, MySQL, Docker, Jenkins, Git",
        "education": "BTech Information Technology, 2019",
    },
    "sarah_lopez": {
        "format": "docx",
        "purpose": "Strong backend match who goes all the way to HIRED (becomes the demo employee).",
        "name": "Sarah Lopez",
        "headline": "Senior Software Engineer — Backend",
        "contact": "sarah.lopez@candidates-demo.com · Madrid, Spain",
        "summary": "Seven years of experience building and operating backend services. Strong on API design, "
        "databases and cloud infrastructure.",
        "experience": [
            ("Senior Software Engineer", "Kestrel Analytics", "2020 – present", [
                "Own the core data API (Python, FastAPI, PostgreSQL) used by 40 internal teams.",
                "Introduced Docker-based local environments and Kubernetes deployments on AWS.",
                "Mentor 3 junior engineers; run the team's incident reviews.",
            ]),
            ("Software Engineer", "Meridian Bank", "2016 – 2020", [
                "Built REST APIs in Python and SQL for the retail banking platform.",
                "Migrated a legacy Oracle reporting database to PostgreSQL with zero downtime.",
            ]),
        ],
        "skills": "Python, FastAPI, REST APIs, SQL, PostgreSQL, Docker, Kubernetes, AWS, Terraform, Git",
        "education": "MSc Software Engineering, Universidad Politécnica de Madrid, 2016",
    },
    "fatima_zahra": {
        "format": "pdf",
        "purpose": "Strong 4-year backend resume; used to demonstrate REJECTING a candidate and the rejection email.",
        "name": "Fatima Zahra",
        "headline": "Backend Developer",
        "contact": "fatima.zahra@candidates-demo.com · Casablanca, Morocco",
        "summary": "Backend developer with 4 years of experience in Python web services and relational databases.",
        "experience": [
            ("Backend Developer", "Atlas Commerce", "2022 – present", [
                "Build REST APIs in Python (FastAPI) and PostgreSQL for an e-commerce platform.",
                "Containerise services with Docker; write integration tests with pytest.",
                "Optimise SQL queries for the order-history service.",
            ]),
            ("Junior Developer", "Sahara Digital", "2020 – 2022", [
                "Developed Python scripts and REST endpoints for client dashboards.",
            ]),
        ],
        "skills": "Python, FastAPI, REST APIs, SQL, PostgreSQL, Docker, pytest, Git",
        "education": "Licence en Informatique, Université Hassan II, 2020",
    },
    # ---------------------------------------------------------------- partial / weak backend
    "marcus_webb": {
        "format": "txt",
        "purpose": "Mid match: junior-ish (2 years), Python and SQL but no PostgreSQL or Docker.",
        "name": "Marcus Webb",
        "headline": "Junior Python Developer",
        "contact": "marcus.webb@candidates-demo.com · Manchester, UK",
        "summary": "Python developer with 2 years of experience building internal tools and simple web APIs.",
        "experience": [
            ("Python Developer", "Greenfield Retail", "2023 – present", [
                "Build internal tools and small REST APIs in Python (Flask).",
                "Write SQL queries against a MySQL database for stock reports.",
            ]),
            ("IT Support Analyst", "Greenfield Retail", "2021 – 2023", [
                "First-line support; automated routine tasks with Python scripts.",
            ]),
        ],
        "skills": "Python, Flask, REST APIs, SQL, MySQL, Git, Linux basics",
        "education": "HND Computing, Manchester College, 2021",
    },
    "chloe_dubois": {
        "format": "pdf",
        "purpose": "Below the experience minimum: recent graduate, 0 years, with course projects.",
        "name": "Chloé Dubois",
        "headline": "Computer Science Graduate",
        "contact": "chloe.dubois@candidates-demo.com · Lille, France",
        "summary": "Recent graduate looking for a first backend role. Eager to learn and ship.",
        "experience": [
            ("Final-year project", "Université de Lille", "2024", [
                "Built a REST API in Python (FastAPI) with a PostgreSQL database for a library app.",
                "Wrote SQL queries and basic database migrations.",
            ]),
            ("Intern (3 months)", "Nord Numérique", "Summer 2023", [
                "Fixed bugs in a Python/Django project and wrote unit tests.",
            ]),
        ],
        "skills": "Python, FastAPI, Django, SQL, PostgreSQL, Git",
        "education": "MSc Computer Science, Université de Lille, 2024",
    },
    "james_oconnor": {
        "format": "pdf",
        "purpose": "Vague resume: experience described without naming technologies, so skills come out as "
        "'insufficient evidence' (the honest third state) rather than 'not matched'.",
        "name": "James O'Connor",
        "headline": "Software Professional",
        "contact": "james.oconnor@candidates-demo.com · Dublin, Ireland",
        "summary": "Experienced technology professional with a track record of delivering solutions for "
        "demanding clients. Strong communicator and quick learner.",
        "experience": [
            ("Technical Lead", "Emerald Consulting", "2018 – present", [
                "Led delivery of software solutions for enterprise clients across several industries.",
                "Worked closely with stakeholders to define requirements and ensure on-time delivery.",
                "Responsible for system design, quality and mentoring of a team of developers.",
            ]),
            ("Developer", "Celtic Software", "2014 – 2018", [
                "Developed and maintained back-end systems and data integrations.",
                "Contributed to architecture decisions and code reviews.",
            ]),
        ],
        "skills": "Software development, system design, team leadership, stakeholder management",
        "education": "BSc Computing, Dublin Institute of Technology, 2014",
    },
    "daniel_kim": {
        "format": "pdf",
        "purpose": "Applies to two jobs with ONE resume (Backend and DevOps) to show a resume is reusable.",
        "name": "Daniel Kim",
        "headline": "Software / Infrastructure Engineer",
        "contact": "daniel.kim@candidates-demo.com · Toronto, Canada",
        "summary": "Engineer with 4 years across backend development and infrastructure.",
        "experience": [
            ("Software Engineer", "Maple Cloud", "2021 – present", [
                "Develop Python services and REST APIs backed by PostgreSQL.",
                "Maintain Docker images and CI/CD pipelines in GitLab CI.",
                "Run workloads on AWS (ECS, RDS).",
            ]),
            ("Systems Administrator", "Northern Hosting", "2019 – 2021", [
                "Administered Linux servers and automated deployments with shell scripts.",
            ]),
        ],
        "skills": "Python, REST APIs, SQL, PostgreSQL, Docker, GitLab CI, AWS, Linux, Bash",
        "education": "BSc Computer Engineering, University of Waterloo, 2019",
    },
    # ---------------------------------------------------------------- frontend
    "lina_haddad": {
        "format": "pdf",
        "purpose": "A frontend specialist; applies to Frontend (strong) AND Backend (weak) with one resume.",
        "name": "Lina Haddad",
        "headline": "Frontend Engineer",
        "contact": "lina.haddad@candidates-demo.com · Tunis, Tunisia",
        "summary": "Frontend engineer with 4 years building accessible, performant web interfaces.",
        "experience": [
            ("Frontend Engineer", "Carthage Digital", "2022 – present", [
                "Build product interfaces in React and TypeScript with Next.js.",
                "Championed accessibility (WCAG 2.1) and cut bundle size by 30%.",
                "Consume REST APIs and wrote a small Node.js backend-for-frontend.",
            ]),
            ("Web Developer", "Mediterranean Studio", "2020 – 2022", [
                "Delivered responsive sites with HTML, CSS (Tailwind) and JavaScript.",
            ]),
        ],
        "skills": "TypeScript, React, Next.js, CSS, Tailwind, REST APIs, accessibility, Jest, basic Python",
        "education": "Engineering degree in Computer Science, Université de Tunis El Manar, 2020",
    },
    "nadia_petrova": {
        "format": "docx",
        "purpose": "Designer-developer hybrid applying to Frontend: moderate score, no TypeScript.",
        "name": "Nadia Petrova",
        "headline": "Product Designer & Front-End Developer",
        "contact": "nadia.petrova@candidates-demo.com · Sofia, Bulgaria",
        "summary": "Designer who codes: 3 years designing in Figma and implementing interfaces.",
        "experience": [
            ("Product Designer", "Rila Apps", "2022 – present", [
                "Design systems and prototypes in Figma; run usability tests.",
                "Implement UI in React and CSS alongside the engineering team.",
            ]),
            ("Junior Front-End Developer", "Balkan Web", "2021 – 2022", [
                "Built landing pages in HTML, CSS and JavaScript.",
            ]),
        ],
        "skills": "Figma, UX research, React, CSS, JavaScript, HTML",
        "education": "BA Interaction Design, 2021",
    },
    "hannah_schmidt": {
        "format": "pdf",
        "purpose": "Frontend applicant with a solid readable resume (her unreadable scanned one is uploaded too).",
        "name": "Hannah Schmidt",
        "headline": "Frontend Developer",
        "contact": "hannah.schmidt@candidates-demo.com · Berlin, Germany",
        "summary": "Frontend developer, 3 years, TypeScript and React.",
        "experience": [
            ("Frontend Developer", "Spree Software", "2022 – present", [
                "Develop customer-facing features in React and TypeScript.",
                "Integrate REST APIs and write component tests.",
                "Styling with CSS modules; improved accessibility scores.",
            ]),
        ],
        "skills": "TypeScript, React, CSS, REST APIs, Jest, Git",
        "education": "BSc Media Informatics, 2021",
    },
    # ---------------------------------------------------------------- ML
    "wei_zhang": {
        "format": "pdf",
        "purpose": "Strong ML match; goes to the OFFER stage.",
        "name": "Wei Zhang",
        "headline": "Machine Learning Engineer",
        "contact": "wei.zhang@candidates-demo.com · Singapore",
        "summary": "ML engineer with 5 years taking models from research to production.",
        "experience": [
            ("Machine Learning Engineer", "Lionfish AI", "2021 – present", [
                "Train and deploy computer-vision models in PyTorch; serve them behind FastAPI on AWS.",
                "Built the MLOps pipeline (MLflow, Docker, GitHub Actions) for model versioning and rollout.",
                "Query and prepare training data with SQL and Python.",
            ]),
            ("Data Scientist", "Straits Analytics", "2019 – 2021", [
                "Machine learning models for demand forecasting in Python (scikit-learn).",
            ]),
        ],
        "skills": "Python, PyTorch, Machine Learning, SQL, MLOps, MLflow, Docker, AWS, scikit-learn",
        "education": "MSc Artificial Intelligence, National University of Singapore, 2019",
    },
    "tomas_rivera": {
        "format": "pdf",
        "purpose": "ML specialist who applies to ML (good) and Backend (partial: no Docker or PostgreSQL).",
        "name": "Tomás Rivera",
        "headline": "Machine Learning Engineer",
        "contact": "tomas.rivera@candidates-demo.com · Buenos Aires, Argentina",
        "summary": "Machine learning engineer, 4 years, focused on NLP.",
        "experience": [
            ("Machine Learning Engineer", "Pampa Labs", "2021 – present", [
                "Fine-tune and evaluate NLP models in PyTorch; Python for data pipelines.",
                "SQL for feature extraction from a data warehouse.",
                "Expose models through a small REST API (Flask).",
            ]),
            ("Data Analyst", "Rioplatense Media", "2019 – 2021", [
                "Analysis in Python and SQL; dashboards for editorial teams.",
            ]),
        ],
        "skills": "Python, PyTorch, Machine Learning, NLP, SQL, Flask, REST APIs, Git",
        "education": "BSc Mathematics, Universidad de Buenos Aires, 2019",
    },
    # ---------------------------------------------------------------- devops
    "ahmed_benali": {
        "format": "pdf",
        "purpose": "Strong DevOps match; also applies to Backend (partial).",
        "name": "Ahmed Benali",
        "headline": "DevOps Engineer",
        "contact": "ahmed.benali@candidates-demo.com · Oran, Algeria",
        "summary": "DevOps engineer with 6 years automating infrastructure and delivery pipelines.",
        "experience": [
            ("DevOps Engineer", "Sahel Cloud", "2020 – present", [
                "Run production Kubernetes clusters on AWS (EKS); define infrastructure with Terraform.",
                "Build CI/CD pipelines in GitLab CI and GitHub Actions; containerise apps with Docker.",
                "Administer Linux fleets; write automation in Python and Bash.",
            ]),
            ("Systems Engineer", "Maghreb Telecom", "2017 – 2020", [
                "Linux administration, monitoring (Prometheus, Grafana) and incident response.",
            ]),
        ],
        "skills": "Docker, Kubernetes, CI/CD, AWS, Linux, Terraform, Python, Bash, Prometheus",
        "education": "Engineering degree in Computer Science, USTO Oran, 2017",
    },
    # ---------------------------------------------------------------- other companies
    "elena_rossi": {
        "format": "pdf",
        "purpose": "Strong match for Helix Health's Data Analyst (a second company: tests data isolation).",
        "name": "Elena Rossi",
        "headline": "Healthcare Data Analyst",
        "contact": "elena.rossi@candidates-demo.com · Milan, Italy",
        "summary": "Data analyst with 4 years in healthcare analytics.",
        "experience": [
            ("Data Analyst", "Lombardia Health Network", "2021 – present", [
                "Analyse patient-flow data with SQL and Python (pandas); build Tableau dashboards for clinicians.",
                "Work with hospital data under strict privacy rules (GDPR).",
            ]),
            ("Junior Analyst", "Milano Insights", "2019 – 2021", [
                "Reporting in SQL and Excel for pharmaceutical clients.",
            ]),
        ],
        "skills": "SQL, Python, pandas, Tableau, healthcare data, GDPR",
        "education": "MSc Statistics, Politecnico di Milano, 2019",
    },
    "omar_khalil": {
        "format": "txt",
        "purpose": "Applies to Helix Health's Clinical Product Manager (5+ years required).",
        "name": "Omar Khalil",
        "headline": "Product Manager, Digital Health",
        "contact": "omar.khalil@candidates-demo.com · Cairo, Egypt",
        "summary": "Product manager with 7 years in digital health, from discovery to launch.",
        "experience": [
            ("Senior Product Manager", "Nile Health", "2019 – present", [
                "Own the roadmap of a patient-booking app (400k users); product management with clinicians.",
                "Run discovery, write specifications and measure outcomes with product analytics.",
            ]),
            ("Product Manager", "Cairo Medtech", "2016 – 2019", [
                "Launched a telemedicine product; coordinated compliance with regulators.",
            ]),
        ],
        "skills": "Product management, roadmapping, user research, healthcare, analytics, stakeholder management",
        "education": "MBA, American University in Cairo, 2016",
    },
}

# An image-only PDF (no extractable text), uploaded by Hannah Schmidt to show
# the "could not be read" state. Built by build_assets.py, not from text.
SCANNED_RESUME = "hannah_schmidt_scanned"
