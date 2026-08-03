"""
Prompt construction for the Communication Agent.

Content safety guardrail (structural, not just an instruction): these
builders accept only `candidate_first_name`, `job_title`,
`company_name`, and — for rejection only — an optional `strengths` list.
There is no parameter for score, missing_skills, potential_concerns, or
match_state anywhere in either function signature. This mirrors the
same discipline already established for candidate-facing exposure
elsewhere in this codebase (see
tests/test_candidate_analysis_exposure.py): the safest way to guarantee
scoring internals never leak into candidate-facing text is to never let
the prompt-building code have access to them in the first place, not to
rely on an instruction telling the model to omit them.

`strengths` (when passed) are genuine positive observations from a
completed ResumeAnalysis, used only as flavor for a warmer, more
specific rejection — never as a justification for the rejection itself,
and the prompt explicitly forbids explaining *why* the candidate wasn't
selected.

Versioned exactly like resume_intelligence/prompts.py — bump the
version string whenever prompt text changes meaningfully.
"""

from app.core.llm_provider import LLMMessage

REJECTION_PROMPT_VERSION = "rejection_email_v1"
INTERVIEW_INVITATION_PROMPT_VERSION = "interview_invitation_email_v1"

_TONE_INSTRUCTIONS = """
Write in a warm, professional, human tone — never robotic or generic-sounding
form-letter language. Keep it concise. Do not use placeholder brackets like
[Company Name] — use the real values provided below directly.
""".strip()


def build_rejection_prompt(
    *,
    candidate_first_name: str,
    job_title: str,
    company_name: str,
    strengths: list[str] | None = None,
) -> list[LLMMessage]:
    system = LLMMessage(
        role="system",
        content=(
            "You are a recruiting assistant drafting a rejection email on behalf of "
            "a recruiter. The recruiter will review and edit this draft before it is "
            "ever sent — you are not sending anything yourself.\n\n"
            "Rules:\n"
            "- Be respectful, warm, and brief. Thank the candidate for their time.\n"
            "- Do NOT explain, imply, or hint at why the candidate was not selected. "
            "Never mention a score, a skill gap, an evaluation, or a comparison to "
            "other candidates.\n"
            "- If strengths are provided below, you may reference them briefly and "
            "genuinely (e.g. wishing them well given a named skill), but never frame "
            "them as 'you were strong in X but...' — no 'but'.\n"
            "- Leave the door open for future roles if genuinely warranted, without "
            "being generic filler.\n\n"
            f"{_TONE_INSTRUCTIONS}"
        ),
    )
    user_content = (
        f"Candidate first name: {candidate_first_name}\n"
        f"Job title they applied for: {job_title}\n"
        f"Company name: {company_name}\n"
    )
    if strengths:
        user_content += f"Candidate's genuine strengths (for warm color only, not justification): {strengths}\n"
    user = LLMMessage(role="user", content=user_content)
    return [system, user]


def build_interview_invitation_prompt(
    *,
    candidate_first_name: str,
    job_title: str,
    company_name: str,
) -> list[LLMMessage]:
    system = LLMMessage(
        role="system",
        content=(
            "You are a recruiting assistant drafting an interview invitation email "
            "on behalf of a recruiter. The recruiter will review and edit this draft "
            "before it is ever sent.\n\n"
            "Rules:\n"
            "- Be warm, professional, and enthusiastic without overdoing it.\n"
            "- Do NOT invent a specific date, time, or interview format (video call, "
            "phone, in-person) — no scheduling details exist yet. Say the recruiter "
            "will follow up shortly to coordinate a time.\n"
            "- Do NOT mention a score or evaluation of any kind.\n\n"
            f"{_TONE_INSTRUCTIONS}"
        ),
    )
    user = LLMMessage(
        role="user",
        content=(
            f"Candidate first name: {candidate_first_name}\n"
            f"Job title: {job_title}\n"
            f"Company name: {company_name}\n"
        ),
    )
    return [system, user]
