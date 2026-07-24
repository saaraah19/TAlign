"""
Every SQLAlchemy model must be importable from here — Alembic's env.py
imports this module to populate `Base.metadata` for autogenerate. A model
defined but not imported here is invisible to migrations.
"""

from app.models.application import Application
from app.models.company import Company
from app.models.job import Job
from app.models.parsed_resume import ParsedResume
from app.models.resume import Resume
from app.models.resume_analysis import ResumeAnalysis
from app.models.role import Role, UserRole
from app.models.user import User

__all__ = [
    "Application",
    "Company",
    "Job",
    "ParsedResume",
    "Resume",
    "ResumeAnalysis",
    "Role",
    "UserRole",
    "User",
]
