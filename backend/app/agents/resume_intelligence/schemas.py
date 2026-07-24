"""
Structured output schemas for the Resume Intelligence pipeline.

Two schemas, matching the two separate LLM calls:
  - ExtractedResumeSchema: output of the "parsing" call (raw resume text
    -> structured skills/experience/education). No score, no job
    context involved — this call knows nothing about any job.
  - AlignmentReasoningSchema: output of the "alignment reasoning" call
    (structured resume + job requirements -> per-skill judgments,
    experience fit, strengths/concerns/explanation). Deliberately has
    NO score field — the LLM never outputs a number; overall_score is
    computed by scoring.py from this schema's contents.

`MatchState` is imported from app.models.resume_analysis rather than
redefined here — one enum, used both as the persisted column value and
the structured-output field type, so there's no risk of the two
silently drifting apart.
"""

from pydantic import BaseModel, Field

from app.models.resume_analysis import MatchState


class ExtractedExperienceEntry(BaseModel):
    title: str
    company: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    is_current: bool = False
    description: str | None = None


class ExtractedEducation(BaseModel):
    degree: str
    field: str | None = None
    institution: str | None = None


class ExtractedResumeSchema(BaseModel):
    """Output of the parsing/extraction LLM call."""

    skills: list[str]
    experience_entries: list[ExtractedExperienceEntry]
    total_years_experience: float | None = None
    education: list[ExtractedEducation] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)


class SkillMatchResult(BaseModel):
    skill: str
    match_state: MatchState
    evidence: str | None = Field(
        default=None,
        description="Direct quote or paraphrase from the resume supporting this "
        "classification. Required whenever match_state is MATCHED or "
        "NOT_MATCHED with positive evidence of absence; may be null only "
        "for INSUFFICIENT_EVIDENCE.",
    )


class ExperienceFitResult(BaseModel):
    candidate_relevant_years: float | None = None
    #: None means insufficient evidence to judge — NOT "does not meet
    #: the minimum". See scoring.py for how this affects the score.
    meets_minimum: bool | None = None
    justification: str


class AlignmentReasoningSchema(BaseModel):
    """
    Output of the alignment reasoning LLM call. Deliberately has NO
    overall score field — see module docstring.
    """

    required_skills: list[SkillMatchResult]
    preferred_skills: list[SkillMatchResult]
    experience_fit: ExperienceFitResult
    strengths: list[str] = Field(max_length=5)
    potential_concerns: list[str] = Field(max_length=5)
    explanation: str
