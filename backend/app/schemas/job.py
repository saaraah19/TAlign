"""Job schemas."""

import uuid
from datetime import datetime

from pydantic import AliasPath, BaseModel, ConfigDict, Field, model_validator

from app.models.job import Currency, EmploymentType, JobStatus


class JobCreateRequest(BaseModel):
    title: str = Field(min_length=2, max_length=255)
    description: str = Field(min_length=1)
    employment_type: EmploymentType
    location: str | None = Field(default=None, max_length=255)
    salary_min: int | None = Field(default=None, ge=0)
    salary_max: int | None = Field(default=None, ge=0)
    salary_currency: Currency = Currency.USD

    # --- Recruiter-authored scoring criteria (Slice 4) ---
    # These, not `description`, are what the Resume Intelligence Agent
    # scores against. See app/models/job.py's docstring.
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    min_years_experience: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def _validate_salary_range(self) -> "JobCreateRequest":
        if self.salary_min is not None and self.salary_max is not None:
            if self.salary_min > self.salary_max:
                raise ValueError("salary_min cannot be greater than salary_max.")
        return self


class JobUpdateRequest(BaseModel):
    """
    All fields optional (partial update). Note: sending a field as `null`
    is NOT distinguished from omitting it — both leave the existing value
    unchanged. Clearing an optional field (e.g. removing `location`) is a
    known limitation deferred until a real use case needs it; today no
    field starts non-null and needs clearing in normal usage.
    """

    title: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = Field(default=None, min_length=1)
    employment_type: EmploymentType | None = None
    location: str | None = Field(default=None, max_length=255)
    salary_min: int | None = Field(default=None, ge=0)
    salary_max: int | None = Field(default=None, ge=0)
    salary_currency: Currency | None = None
    required_skills: list[str] | None = None
    preferred_skills: list[str] | None = None
    min_years_experience: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def _validate_salary_range(self) -> "JobUpdateRequest":
        if self.salary_min is not None and self.salary_max is not None:
            if self.salary_min > self.salary_max:
                raise ValueError("salary_min cannot be greater than salary_max.")
        return self


class JobStatusTransitionRequest(BaseModel):
    target_status: JobStatus


class JobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID
    created_by: uuid.UUID | None
    title: str
    description: str
    employment_type: EmploymentType
    location: str | None
    salary_min: int | None
    salary_max: int | None
    salary_currency: Currency
    status: JobStatus
    required_skills: list[str]
    preferred_skills: list[str]
    min_years_experience: int | None
    created_at: datetime
    updated_at: datetime


class JobWithStatsRead(JobRead):
    """
    JobRead plus per-job pipeline stats, for the Jobs list page's cards.
    Not just `JobRead` itself because these two fields aren't columns on
    Job -- they're computed by aggregating Applications (see
    ApplicationRepository.count_by_status_grouped_by_job) and can't be
    produced by a plain `model_validate(job)` the way every other field
    here can.
    """

    applicant_count: int
    stage_counts: dict[str, int]


class JobListResponse(BaseModel):
    items: list[JobWithStatsRead]
    total: int
    page: int
    page_size: int


class PublicJobRead(BaseModel):
    """
    A job as an anonymous visitor sees it on the public job board.

    Deliberately NOT `JobRead`. `JobRead` is the staff view and carries
    `company_id`, `created_by` (the internal user id of the recruiter who
    wrote the job) and `status` — none of which a stranger browsing
    careers needs, and the user id in particular is internal data that
    should not be handed to the open internet. What the public DOES need
    and `JobRead` lacks is the employer's name: before this schema a
    candidate could browse and apply to a role without ever being shown
    which company posted it.

    Same convention as the candidate-facing analysis schemas: a field
    that is not declared here cannot leak, whatever a future caller
    forgets to strip.

    `company_name` is read straight off the ORM object (`job.company.name`)
    via the AliasPath, so the repository MUST load `Job.company` eagerly
    (see JobRepository.list_open / get_open_with_company) — touching an
    unloaded relationship in async SQLAlchemy raises MissingGreenlet.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_name: str = Field(validation_alias=AliasPath("company", "name"))
    title: str
    description: str
    employment_type: EmploymentType
    location: str | None
    salary_min: int | None
    salary_max: int | None
    salary_currency: Currency
    required_skills: list[str]
    preferred_skills: list[str]
    min_years_experience: int | None
    created_at: datetime


class PublicJobListResponse(BaseModel):
    """
    The candidate-facing job list. Deliberately NOT `JobListResponse`:
    that one carries `JobWithStatsRead` items (applicant counts, per-stage
    counts), which are recruiter-only data. A separate type means those
    fields are structurally absent, and the public endpoint can't be broken
    again by a change to the recruiter's list.
    """

    items: list[PublicJobRead]
    total: int
    page: int
    page_size: int
