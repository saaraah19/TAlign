"""
Domain exceptions.

Services raise these — never `fastapi.HTTPException` (that would couple
`app/services/` to the HTTP layer, violating "business logic belongs to
domain services" and making services untestable without a request
context). `app/main.py` registers one exception handler per base class
here, translating domain errors to HTTP responses at the boundary.
"""


class TalignError(Exception):
    """Base for every domain exception. Subclasses set `http_status`."""

    http_status: int = 400

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class ConflictError(TalignError):
    http_status = 409


class AuthenticationError(TalignError):
    http_status = 401


class AuthorizationError(TalignError):
    http_status = 403


class DomainValidationError(TalignError):
    """
    Business-rule validation failure — distinct from FastAPI/Pydantic's
    request-shape validation (which already returns 422 automatically).
    This is for rules that depend on more than one field or on database
    state, e.g. "candidates must not have a company_id".
    """

    http_status = 422


class NotFoundError(TalignError):
    http_status = 404


# --- Auth-specific exceptions ---


class EmailAlreadyExistsError(ConflictError):
    pass


class InvalidCredentialsError(AuthenticationError):
    pass


class InactiveAccountError(AuthenticationError):
    pass


class InvalidTokenError(AuthenticationError):
    pass


class InvalidCompanyAssignmentError(DomainValidationError):
    """
    Raised when a candidate is associated with a company_id, or an
    internal user is created without one. Mirrors the DB-level
    ck_users_company_assignment constraint — this is the service-layer
    half of the two-layer enforcement.
    """

    pass


# --- Job-specific exceptions ---


class InvalidJobStatusTransitionError(DomainValidationError):
    """
    Raised when a requested Job status transition isn't in the allowed
    graph (DRAFT -> OPEN -> CLOSED -> ARCHIVED, no skipping, no going
    backward). See JobService._validate_transition — this is the
    service-layer enforcement; the DB's ck_jobs_status_valid only checks
    that the value is a known status, not that the transition is legal.
    """

    pass


# --- Application-specific exceptions ---


class DuplicateApplicationError(ConflictError):
    """
    Raised when a candidate attempts to apply to a job they've already
    applied to. Mirrors the DB-level uq_applications_candidate_job
    unique constraint — this is the service-layer half, checked before
    insert; the constraint is the last line of defense against a race.
    """

    pass


class JobNotOpenForApplicationsError(DomainValidationError):
    """Raised when applying to a job whose status isn't OPEN."""

    pass


class InvalidApplicationStatusTransitionError(DomainValidationError):
    """
    Raised when a requested Application status transition isn't in the
    allowed graph. See ApplicationService._validate_transition.
    """

    pass


class InvalidCandidateError(DomainValidationError):
    """
    Raised if a non-candidate account somehow reaches application
    submission. Defense in depth — RBAC (require_roles(Role.CANDIDATE))
    already prevents this at the API layer; this is the service not
    trusting that its caller enforced its own precondition, same
    reasoning as JobService._assert_internal_with_company.
    """

    pass


# --- Resume / Resume Intelligence exceptions ---


class UnsupportedFileTypeError(DomainValidationError):
    """Raised when an uploaded resume's content-type isn't in the configured allow-list."""

    pass


class FileTooLargeError(DomainValidationError):
    """Raised when an uploaded resume exceeds settings.max_resume_file_size_bytes."""

    pass


class ResumeTextExtractionError(DomainValidationError):
    """
    Raised when the deterministic file->text step fails (corrupt file,
    unreadable PDF, etc). Distinct from LLM failures — this happens
    before any LLM call, with a library (pypdf/python-docx), not a model.
    """

    pass


class LLMProviderError(TalignError):
    """
    Raised when the underlying LLM call itself fails (provider error,
    timeout, rate limit). Wraps whatever the provider raised so callers
    only ever handle Talign's own exception hierarchy — mirrors
    core/security.py's InvalidTokenError wrapping jose's JWTError.
    """

    http_status = 502


class InvalidStructuredOutputError(TalignError):
    """
    Raised when an LLM response fails schema validation even after the
    one permitted re-prompt retry (see ResumeIntelligenceAgent). This is
    the exception that makes "never parse arbitrary LLM prose" real:
    if the model's output can't be validated against the Pydantic
    schema, this is raised instead of attempting to salvage a partial
    answer from free text.
    """

    http_status = 502


class ResumeNotOwnedError(NotFoundError):
    """
    Raised when a candidate references a resume_id that isn't theirs.
    Subclasses NotFoundError (404), not AuthorizationError (403) — same
    reasoning as cross-company Job/Application access in Slices 2-3:
    don't confirm a resume with that ID exists at all.
    """

    pass


# --- Communication Agent exceptions ---


class EmailAlreadySentError(ConflictError):
    """
    Raised when attempting to edit, regenerate, or re-send an Email
    whose status is already SENT. A sent email is a historical record
    — see app/models/email.py's docstring on the DRAFT/SENT lifecycle.
    """

    pass


# --- Knowledge Agent exceptions ---


class DocumentProcessingError(TalignError):
    """
    Raised when any step of the knowledge document pipeline fails
    (text extraction, chunking producing zero chunks, or embedding).
    Caught by KnowledgeDocumentService, which persists it as
    KnowledgeDocument.status = FAILED with the message recorded — never
    left as an unhandled exception, same discipline as Resume's
    PARSE_FAILED handling.
    """

    http_status = 422


class KnowledgeAnswerValidationError(TalignError):
    """
    Raised when the LLM's structured answer cites a chunk_id that was
    never actually provided in its context — the RAG-specific structural
    anti-hallucination check described in
    docs/06_slice6_knowledge_agent.md section 7. Distinct from
    InvalidStructuredOutputError (which is a schema-shape failure) —
    this is a schema-VALID response whose *content* fabricated a source,
    which is arguably worse.
    """

    http_status = 502
