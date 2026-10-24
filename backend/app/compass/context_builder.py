"""
Compass context builder.

This is where "building context" (one of Compass's stated jobs) actually
happens — by calling existing, already-RBAC-respecting services
(ApplicationService, ResumeAnalysisService), never the database
directly. The output is a plain dict handed to an Agent via
`AgentContext.payload` — agents never see a service or a DB session,
only data (see app/agents/base.py's AgentContext, and
ResumeIntelligenceAgent/ApplicationStatusAgent's own docstrings on
receiving "structured context rather than directly querying arbitrary
database tables").

Kept as a separate class from `Compass` itself so the routing logic in
compass.py stays readable as pure orchestration — this class does the
one substantive step (fetching and shaping data) in between "select a
capability" and "invoke the agent."
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.roles import Role
from app.models.user import User
from app.schemas.resume_analysis import ResumeAnalysisRead
from app.services.application_service import ApplicationService
from app.services.resume_analysis_service import ResumeAnalysisService


class CompassContextBuilder:
    def __init__(self, db: AsyncSession) -> None:
        self._applications = ApplicationService(db)
        self._analyses = ResumeAnalysisService(db)

    async def build_for_application_status(
        self, *, application_id: uuid.UUID, candidate: User
    ) -> dict:
        application = await self._applications.get_my_application(
            application_id=application_id, candidate=candidate
        )
        return {"job_title": application.job.title, "status": application.status}

    async def build_for_explain_analysis(
        self, *, application_id: uuid.UUID, acting_user: User, question: str, role: Role
    ) -> dict:
        analysis = await self._analyses.get_latest_completed_for_company(
            application_id=application_id, acting_user=acting_user
        )
        analysis_read = ResumeAnalysisRead.model_validate(analysis)

        return {
            "question": question,
            "audience_role": role.value,
            "analysis": {
                "overall_score": analysis_read.overall_score,
                "required_skills_result": [
                    r.model_dump() for r in analysis_read.required_skills_result
                ],
                "preferred_skills_result": [
                    r.model_dump() for r in analysis_read.preferred_skills_result
                ],
                "experience_fit": (
                    analysis_read.experience_fit.model_dump()
                    if analysis_read.experience_fit
                    else {}
                ),
                "strengths": analysis_read.strengths,
                "potential_concerns": analysis_read.potential_concerns,
                "explanation": analysis_read.explanation or "",
            },
        }
