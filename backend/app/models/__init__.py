"""
Every SQLAlchemy model must be importable from here — Alembic's env.py
imports this module to populate `Base.metadata` for autogenerate. A model
defined but not imported here is invisible to migrations.
"""

from app.models.application import Application
from app.models.company import Company
from app.models.dashboard_brief import DashboardBrief
from app.models.email import Email
from app.models.employee import Employee
from app.models.job import Job
from app.models.knowledge_chunk import KnowledgeChunk
from app.models.knowledge_document import KnowledgeDocument
from app.models.onboarding_task import OnboardingTask
from app.models.parsed_resume import ParsedResume
from app.models.resume import Resume
from app.models.resume_analysis import ResumeAnalysis
from app.models.role import Role, UserRole
from app.models.user import User
from app.models.workflow_run import WorkflowRun

__all__ = [
    "Application",
    "Company",
    "DashboardBrief",
    "Email",
    "Employee",
    "Job",
    "KnowledgeChunk",
    "KnowledgeDocument",
    "OnboardingTask",
    "ParsedResume",
    "Resume",
    "ResumeAnalysis",
    "Role",
    "User",
    "UserRole",
    "WorkflowRun",
]
