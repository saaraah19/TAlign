"""
Prompt construction for the Resume Intelligence pipeline.

Two versioned prompt builders, matching the two LLM calls. Versions are
bumped whenever the prompt text changes meaningfully — persisted on
every ParsedResume/ResumeAnalysis row (prompt_version) so historical
results stay traceable to the exact instructions that produced them,
same discipline as SCORING_ALGORITHM_VERSION in scoring.py.

PII minimization (best-effort, documented limitation): neither prompt
ever includes the candidate's name, email, or any other User field —
only resume text and job requirements are sent. Resume text ITSELF may
still contain the candidate's name (most resumes open with one) — full
PII redaction from free-text resume content is a real NLP problem
outside this slice's scope, so this is a best-effort measure, not a
guarantee, and is documented as such rather than silently assumed complete.
"""

from app.core.llm_provider import LLMMessage

EXTRACTION_PROMPT_VERSION = "resume_extraction_v1"
ALIGNMENT_PROMPT_VERSION = "alignment_analysis_v1"

_FAIRNESS_INSTRUCTIONS = """
You must evaluate only job-relevant qualifications: skills, experience, and
education/certifications where explicitly relevant to the role.

You must NOT use, infer, mention, or let your judgment be influenced by any
of the following, even if apparent from the resume text:
- gender
- age
- race or ethnicity
- religion
- marital or family status
- pregnancy
- disability (unless the job explicitly concerns an accommodation workflow)
- nationality (unless legally required for the specific role)
- physical appearance
- the candidate's name as an inferred proxy for any of the above

If any such information appears in the resume, ignore it entirely. Base
every judgment strictly on demonstrated skills, experience, and
qualifications relevant to the job.
""".strip()


def build_extraction_prompt(resume_text: str) -> list[LLMMessage]:
    system = LLMMessage(
        role="system",
        content=(
            "You are a resume-parsing assistant. Extract structured information "
            "from the resume text provided. Extract only what is explicitly "
            "stated or can be directly and confidently inferred (e.g. computing "
            "total years of experience from listed date ranges). Do not "
            "invent skills, roles, or experience not present in the text.\n\n"
            f"{_FAIRNESS_INSTRUCTIONS}"
        ),
    )
    user = LLMMessage(role="user", content=f"Resume text:\n\n{resume_text}")
    return [system, user]


def build_alignment_prompt(
    *,
    extracted_skills: list[str],
    experience_summary: str,
    total_years_experience: float | None,
    required_skills: list[str],
    preferred_skills: list[str],
    min_years_experience: int | None,
    job_description_context: str,
) -> list[LLMMessage]:
    """
    `required_skills` / `preferred_skills` / `min_years_experience` are the
    OFFICIAL scoring criteria (recruiter-authored on the Job).
    `job_description_context` is the job's free-text description, included
    strictly as background context for interpreting evidence — the prompt
    explicitly tells the model not to treat it as criteria, per the
    product decision that only the structured fields above define what's
    being scored.
    """
    system = LLMMessage(
        role="system",
        content=(
            "You are a hiring-alignment assistant. You will be given a "
            "candidate's extracted resume information and a job's requirements. "
            "Your job is to classify, with evidence, whether the candidate's "
            "resume demonstrates each required and preferred skill, and whether "
            "their experience meets the stated minimum.\n\n"
            "For each skill, classify it as exactly one of: 'matched' (the "
            "resume provides clear evidence), 'not_matched' (the resume "
            "provides evidence the candidate does NOT have this skill, or "
            "the skill is contradicted), or 'insufficient_evidence' (the "
            "resume simply does not mention this skill either way — this is "
            "the correct classification whenever you cannot confidently say "
            "matched OR not_matched; do NOT default to not_matched just "
            "because a skill isn't mentioned).\n\n"
            "The job's structured required_skills, preferred_skills, and "
            "min_years_experience below are the OFFICIAL scoring criteria — "
            "evaluate against exactly these. The job description text is "
            "provided only as background context to help you interpret the "
            "role and the resume's evidence; it is NOT itself a scoring "
            "criterion, and you must not add, remove, or reinterpret the "
            "official skill list based on it.\n\n"
            "You are producing an analytical signal to help a human recruiter, "
            "not making a hiring decision. Do not recommend acceptance or "
            "rejection.\n\n"
            f"{_FAIRNESS_INSTRUCTIONS}"
        ),
    )

    user = LLMMessage(
        role="user",
        content=(
            f"Job's official required skills: {required_skills}\n"
            f"Job's official preferred skills: {preferred_skills}\n"
            f"Job's official minimum years of experience: {min_years_experience}\n\n"
            f"Job description (context only, not scoring criteria):\n"
            f"{job_description_context}\n\n"
            f"Candidate's extracted skills: {extracted_skills}\n"
            f"Candidate's experience summary: {experience_summary}\n"
            f"Candidate's total years of experience (as extracted): {total_years_experience}\n"
        ),
    )
    return [system, user]


def build_explanation_prompt(
    *,
    question: str,
    audience_role: str,
    overall_score: float,
    required_skills_result: list[dict],
    preferred_skills_result: list[dict],
    experience_fit: dict,
    strengths: list[str],
    potential_concerns: list[str],
    explanation: str,
) -> list[LLMMessage]:
    """
    Builds the prompt for Compass's `explain_analysis` capability —
    narrating an EXISTING, already-persisted analysis. Explicitly
    instructed not to introduce new judgments or change the score; this
    call uses `complete()` (free text), not `complete_structured()`,
    since it's a conversational answer, not a new piece of stored
    intelligence.
    """
    system = LLMMessage(
        role="system",
        content=(
            "You are Compass, Talign's AI assistant. A user is asking about an "
            "existing resume alignment analysis. Answer their question using "
            "ONLY the analysis data provided below — do not invent new "
            "judgments, do not change the score, do not speculate beyond what "
            "the stored analysis says. Speak like a knowledgeable colleague, "
            "not a report generator. Keep the answer concise (2-4 sentences "
            f"unless the question needs more). The audience is a {audience_role}."
        ),
    )
    user = LLMMessage(
        role="user",
        content=(
            f"Stored analysis:\n"
            f"Overall alignment score: {overall_score}/100\n"
            f"Required skills evaluation: {required_skills_result}\n"
            f"Preferred skills evaluation: {preferred_skills_result}\n"
            f"Experience fit: {experience_fit}\n"
            f"Strengths: {strengths}\n"
            f"Potential concerns: {potential_concerns}\n"
            f"Original explanation: {explanation}\n\n"
            f"Question: {question}"
        ),
    )
    return [system, user]
