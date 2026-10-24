"""
DEMO STAND-IN for the AI providers — used only to produce the README screenshots.

This is NOT a language model and not evidence of Gemini's quality. It is a small,
rule-based substitute, built so that the screenshots show plausible, internally
consistent content instead of placeholders:

  * resume extraction  : reads the resume's real text (sections, dates, skills)
  * alignment judgement: checks each required/preferred skill against the
                         candidate's actual skills and experience text
  * knowledge answers  : picks the best-matching sentences from the retrieved
                         policy passages and cites them
  * emails, daily brief, Compass explanations: filled from templates and the
                         facts supplied in the prompt

Because it follows the same rules the real prompts ask of Gemini (never invent,
"insufficient evidence" when a skill is simply not mentioned, no reasons in a
rejection email), the structure of every screen is realistic. The WORDING and
the exact scores are not what Gemini would produce. Never use this against real
data, and never read it as a measurement of AI quality.
"""

from __future__ import annotations

import ast
import hashlib
import math
import re
from collections import Counter

import app.core.llm_provider as lp
from app.core.exceptions import InvalidStructuredOutputError
from app.models.knowledge_chunk import EMBEDDING_DIMENSION

REFERENCE_YEAR = 2026

# Groups of related skills, used to decide between "not matched" and
# "insufficient evidence" when a skill is not mentioned.
FAMILIES = {
    "backend": {"python", "fastapi", "django", "flask", "sql", "postgresql", "rest apis", "java",
                "node.js", "go", "redis", "microservices"},
    "cloud": {"aws", "docker", "kubernetes", "terraform", "gcp", "azure", "ci/cd", "linux",
              "github actions", "monitoring", "prometheus"},
    "frontend": {"react", "typescript", "javascript", "css", "html", "next.js", "tailwind",
                 "tailwindcss", "testing"},
    "ml": {"pytorch", "tensorflow", "scikit-learn", "machine learning", "mlops", "pandas", "numpy",
           "deep learning", "nlp"},
}
ALIASES = {
    "rest apis": ["rest"],
    "sql": ["postgres", "mysql", "sql"],
    "ci/cd": ["github actions", "gitlab ci", "jenkins", "ci/cd"],
    "kubernetes": ["kubernetes", "k8s", "eks"],
    "machine learning": ["machine learning", "ml ", "model training"],
    "mlops": ["mlops", "mlflow", "model deployment"],
    "tailwindcss": ["tailwind"],
}


def _has(skill: str, haystack: str) -> bool:
    keys = [skill.lower()] + ALIASES.get(skill.lower(), [])
    return any(re.search(r"(?<![a-z0-9])" + re.escape(k) + r"(?![a-z0-9])", haystack) for k in keys)


def _split_skills(text: str) -> list[str]:
    return [s.strip() for s in re.split(r",(?![^()]*\))", text.replace("\n", " ")) if s.strip()]


def _sections(text: str) -> dict[str, list[str]]:
    names = {"summary", "experience", "skills", "education", "certifications"}
    out: dict[str, list[str]] = {}
    current = "header"
    for line in text.splitlines():
        if line.strip().lower() in names and not line.startswith(" "):
            current = line.strip().lower()
            out[current] = []
        else:
            out.setdefault(current, []).append(line)
    return out


def _extract_resume(text: str) -> dict:
    sec = _sections(text)
    summary = " ".join(s.strip() for s in sec.get("summary", []) if s.strip())
    skills = _split_skills("\n".join(sec.get("skills", [])))

    entries: list[dict] = []
    current: dict | None = None
    for line in sec.get("experience", []):
        m = re.match(r"^(.+?) — (.+?) \((\d{4})\s*[–-]\s*(present|\d{4})\)\s*$", line.strip())
        if m and not line.startswith(" "):
            current = {
                "title": m.group(1), "company": m.group(2), "start_date": m.group(3),
                "end_date": None if m.group(4) == "present" else m.group(4),
                "is_current": m.group(4) == "present", "description": "",
            }
            entries.append(current)
        elif current is not None and line.strip():
            current["description"] = (current["description"] + " " + line.strip()).strip()

    years = None
    m = re.search(r"(\d+)\+?\s+years", summary)
    if m:
        years = float(m.group(1))
    elif entries:
        years = float(sum(
            (REFERENCE_YEAR if e["is_current"] else int(e["end_date"])) - int(e["start_date"])
            for e in entries
        ))

    education = []
    for line in sec.get("education", []):
        if line.strip():
            parts = [p.strip() for p in line.split(",")]
            education.append({"degree": parts[0], "institution": parts[1] if len(parts) > 1 else None})

    certs = [c.strip() for c in sec.get("certifications", []) if c.strip()]
    return {
        "skills": skills or ["Not stated"],
        "experience_entries": entries or [{"title": "Not stated"}],
        "total_years_experience": years,
        "education": education,
        "certifications": certs,
        "_summary": summary,
    }


def _alignment(prompt: str) -> dict:
    def lst(label: str) -> list[str]:
        m = re.search(label + r": (\[.*?\])\n", prompt)
        return ast.literal_eval(m.group(1)) if m else []

    required = lst("official required skills")
    preferred = lst("official preferred skills")
    cand_skills = lst("extracted skills")
    m = re.search(r"minimum years of experience: (\d+|None)", prompt)
    min_years = int(m.group(1)) if m and m.group(1) != "None" else None
    m = re.search(r"experience summary: (.*?)\nCandidate's total years", prompt, re.S)
    summary = m.group(1).strip() if m else ""
    m = re.search(r"total years of experience \(as extracted\): ([\d.]+|None)", prompt)
    years = float(m.group(1)) if m and m.group(1) != "None" else None

    haystack = (" ".join(cand_skills) + " " + summary).lower()
    sentences = [s.strip() for s in re.split(r"(?<=[.;])\s+|\n", summary) if s.strip()]
    mine = {s.lower() for s in cand_skills}

    def judge(skill: str) -> dict:
        if _has(skill, haystack):
            ev = next((s for s in sentences if _has(skill, s.lower())), None)
            return {"skill": skill, "match_state": "matched",
                    "evidence": (ev or f"Lists {skill} among their skills.")[:220]}
        family = next((f for f, members in FAMILIES.items() if skill.lower() in members), None)
        if family is None or any(
            any(_has(member, k) for k in mine) for member in FAMILIES[family]
        ):
            return {"skill": skill, "match_state": "insufficient_evidence", "evidence": None}
        return {"skill": skill, "match_state": "not_matched",
                "evidence": f"Nothing in the resume points to {skill}; the experience is in other areas."}

    req = [judge(s) for s in required]
    pref = [judge(s) for s in preferred]

    if min_years is None:
        meets, just = None, "No minimum experience was set for this role."
    elif years is None:
        meets, just = None, "The resume does not make the total years of experience clear."
    elif years >= min_years:
        meets, just = True, f"About {years:g} years of experience against a minimum of {min_years}."
    else:
        meets, just = False, f"About {years:g} years of experience, below the {min_years}-year minimum."

    got = [r["skill"] for r in req if r["match_state"] == "matched"]
    gaps = [r["skill"] for r in req if r["match_state"] == "not_matched"]
    unclear = [r["skill"] for r in req if r["match_state"] == "insufficient_evidence"]
    pref_got = [r["skill"] for r in pref if r["match_state"] == "matched"]

    strengths = []
    if got:
        strengths.append(f"Clear, specific evidence for {', '.join(got[:4])}.")
    if meets:
        strengths.append(just)
    if pref_got:
        strengths.append(f"Also brings preferred skills: {', '.join(pref_got[:3])}.")
    concerns = []
    if gaps:
        concerns.append(f"No evidence of {', '.join(gaps[:3])}, which the role requires.")
    if unclear:
        concerns.append(f"The resume does not say whether they have {', '.join(unclear[:3])}; worth asking at interview.")
    if meets is False:
        concerns.append(just)

    covered = len(got)
    explanation = (
        f"The resume gives clear evidence for {covered} of {len(required)} required skills"
        + (f" and {len(pref_got)} of {len(pref)} preferred ones" if preferred else "")
        + f". {just} "
        + ("The main gap is " + ", ".join(gaps[:2]) + "." if gaps
           else "Nothing required is clearly missing." if not unclear
           else "Some required skills are simply not mentioned, so they are marked as insufficient evidence.")
    )
    return {
        "required_skills": req, "preferred_skills": pref,
        "experience_fit": {"candidate_relevant_years": years, "meets_minimum": meets, "justification": just},
        "strengths": strengths[:5], "potential_concerns": concerns[:5], "explanation": explanation.strip(),
    }


_STOP = {"the", "a", "an", "of", "to", "and", "or", "in", "on", "for", "is", "are", "do", "i", "my",
         "me", "we", "you", "it", "that", "this", "with", "as", "at", "by", "be", "can", "how", "what",
         "does", "get", "must", "many", "much", "when", "from", "have", "per", "any", "our", "your"}


def _words(text: str) -> list[str]:
    out = []
    for w in re.findall(r"[a-z0-9]+", text.lower()):
        if w in _STOP or len(w) < 3:
            continue
        out.append(w[:-1] if w.endswith("s") and len(w) > 4 else w)
    return out



_SENTENCE_STARTERS = {"Every", "All", "Each", "Employees", "Staff", "The", "A", "An", "You", "Your", "We",
                      "Our", "Teams", "Requests", "Any", "New", "Business", "Meals", "Northwind"}


def _drop_leading_heading(sentence: str) -> str:
    """Policy text is stored without line breaks, so headings ("Annual leave", "ANNUAL LEAVE ----")
    end up glued to the first sentence. Drop banner lines, then cut at the last seam near the start
    where a capitalised word that typically opens a sentence follows a lowercase word."""
    sentence = re.sub(r"(?:[A-Z][A-Z ]{3,})?\s*-{3,}\s*", " ", sentence).strip()
    cut = 0
    for m in re.finditer(r"(?<=[a-z]) (?=([A-Z][a-z]+) [a-z])", sentence[:90]):
        if m.group(1) in _SENTENCE_STARTERS:
            cut = m.end()
    return sentence[cut:]


def _knowledge(prompt: str) -> dict:
    question = re.search(r"Question: (.*?)\n\nRetrieved", prompt, re.S).group(1).strip()
    chunks = []
    for block in re.split(r"\[Chunk \d+\]\n", prompt)[1:]:
        cid = re.search(r"chunk_id: (\S+)", block).group(1)
        did = re.search(r"document_id: (\S+)", block).group(1)
        title = re.search(r"document_title: (.*)", block).group(1).strip()
        content = block.split("content:\n", 1)[1].strip()
        chunks.append({"chunk_id": cid, "document_id": did, "document_title": title, "content": content})
    q = set(_words(question))
    best, best_score, best_sent = None, 0, []
    for ch in chunks:
        sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", ch["content"]) if len(s.strip()) > 12]
        scored = sorted(((len(q & set(_words(s))), s) for s in sents), reverse=True)
        total = scored[0][0] if scored else 0
        if total > best_score:
            best, best_score, best_sent = ch, total, [scored[0][1]]
    if best is None or best_score == 0:
        return {"answer": "The retrieved passages do not answer this question.", "citations": [], "grounded": False}
    # keep the document's own order so the answer reads naturally
    ordered = [s for s in re.split(r"(?<=[.!?])\s+|\n+", best["content"]) if s.strip() in best_sent]
    answer = " ".join(_drop_leading_heading(s) for s in ordered)
    return {
        "answer": answer, "grounded": True,
        "citations": [{"document_id": best["document_id"], "document_title": best["document_title"],
                       "chunk_id": best["chunk_id"], "excerpt": answer[:900]}],
    }


def _email(system: str, user: str) -> dict:
    first = re.search(r"first name: (.*)", user).group(1).strip()
    job = re.search(r"Job(?: title they applied for| title): (.*)", user).group(1).strip()
    company = re.search(r"Company name: (.*)", user).group(1).strip()
    low = system.lower()
    if "welcome" in low:
        return {"subject": f"Welcome to {company}, {first}!",
                "body": f"Hi {first},\n\nWelcome to {company}! We are delighted that you are joining us as {job}. "
                        f"Over the next few days you will receive your onboarding checklist and an introduction to your team.\n\n"
                        f"If you have any questions before your first day, just reply to this message.\n\nWarm regards,\nThe {company} team"}
    if "invitation" in low or "interview" in low and "reject" not in low:
        return {"subject": f"Interview invitation: {job} at {company}",
                "body": f"Hi {first},\n\nThank you for your interest in the {job} role at {company}. We enjoyed reviewing your application "
                        f"and would like to invite you to an interview.\n\nOur recruiter will follow up shortly to coordinate a time that suits you.\n\n"
                        f"Kind regards,\nThe {company} recruiting team"}
    return {"subject": f"Your application for {job} at {company}",
            "body": f"Hi {first},\n\nThank you for the time you invested in applying for the {job} position at {company}, and for your interest in joining us.\n\n"
                    f"After careful consideration, we have decided not to move forward with your application at this time. "
                    f"We appreciate you sharing your background with us and wish you every success in your search.\n\nKind regards,\nThe {company} recruiting team"}


def _brief(user: str) -> dict:
    awaiting = re.findall(r"- (.+?) for (.+?) \(application_id: (\S+?), waiting (\d+) days\)", user)
    low = re.findall(r"- (.+?): (\d+) applicants", user)
    pend = re.search(r"Draft emails awaiting review/send: (\d+)", user)
    company = re.search(r"Company: (.*)", user).group(1)
    parts = []
    if awaiting:
        longest = max(awaiting, key=lambda a: int(a[3]))
        waited = f", waiting {longest[3]} days" if int(longest[3]) > 0 else ", who applied recently"
        parts.append(f"{len(awaiting)} applications are waiting for a first review. The one to start with is {longest[0]} for {longest[1]}{waited}.")
    if low:
        parts.append(f"{', '.join(n for n, _ in low[:2])} {'has' if len(low) == 1 else 'have'} fewer than five applicants, so it may be worth promoting.")
    if pend and int(pend.group(1)):
        parts.append(f"{pend.group(1)} drafted emails are waiting for your review.")
    actions = [{"label": f"Review {n} for {j}", "application_id": a} for n, j, a, _ in sorted(awaiting, key=lambda x: -int(x[3]))[:3]]
    return {"summary": " ".join(parts) or f"Nothing urgent is waiting at {company} today.", "recommended_actions": actions}


def _explain(user: str) -> str:
    q = re.search(r"Question: (.*)", user, re.S).group(1).strip().lower()
    score = re.search(r"Overall alignment score: ([\d.]+)", user)
    explanation = re.search(r"Original explanation: (.*?)\n\nQuestion", user, re.S)
    concerns = ast.literal_eval(re.search(r"Potential concerns: (\[.*?\])\n", user, re.S).group(1))
    strengths = ast.literal_eval(re.search(r"Strengths: (\[.*?\])\n", user, re.S).group(1))
    if any(w in q for w in ("gap", "missing", "worr", "weak", "concern")):
        return " ".join(concerns) if concerns else "The stored analysis lists no significant gaps for this candidate."
    if any(w in q for w in ("strength", "good", "strong")):
        return " ".join(strengths) if strengths else "The stored analysis does not list standout strengths."
    base = explanation.group(1).strip() if explanation else ""
    return f"The alignment score is {float(score.group(1)):g}/100. {base}".strip()


class DemoLLM(lp.LLMProvider):
    async def complete(self, messages, *, model=None, temperature=0.2):
        return lp.LLMResponse(content=_explain(messages[-1].content), model="demo-standin")

    async def complete_structured(self, messages, *, response_schema, model=None, temperature=0.0):
        name = response_schema.__name__
        system, user = messages[0].content, messages[-1].content
        if name == "ExtractedResumeSchema":
            data = _extract_resume(user.split("Resume text:\n\n", 1)[1])
            data.pop("_summary", None)
        elif name == "AlignmentReasoningSchema":
            data = _alignment(user)
        elif name == "KnowledgeAnswerSchema":
            data = _knowledge(user)
        elif name == "DraftEmailSchema":
            data = _email(system, user)
        elif name == "DashboardBriefSchema":
            data = _brief(user)
        else:
            raise InvalidStructuredOutputError(f"demo stand-in has no handler for {name}")
        try:
            return response_schema.model_validate(data)
        except Exception as exc:
            raise InvalidStructuredOutputError(f"demo stand-in output invalid for {name}: {exc}") from exc


class DemoEmbeddings(lp.EmbeddingProvider):
    """
    A demo-only retrieval oracle, not a semantic embedding.

    It remembers every passage it has indexed. A question that shares at least two content words
    with some passages gets a vector pointing toward those passages (more shared words, stronger
    pull), so the real application logic downstream (company filtering, the relevance floor, the
    confidence bands, citation checks) runs on top of plausible similarities. A question that
    shares fewer than two words with every passage gets an unrelated vector, so it correctly
    falls under the app's relevance floor and produces the "I don't have information" answer.
    Real Gemini embeddings behave very differently.
    """

    def __init__(self) -> None:
        self._passages: list[tuple[list[float], set[str]]] = []

    @staticmethod
    def _unit(words: list[str]) -> list[float]:
        raw = [0.0] * EMBEDDING_DIMENSION
        for w in set(words):
            raw[int.from_bytes(hashlib.sha256(w.encode()).digest()[:4], "big") % EMBEDDING_DIMENSION] += 1.0
        norm = math.sqrt(sum(x * x for x in raw)) or 1.0
        return [x / norm for x in raw]

    async def embed_documents(self, texts):
        out = []
        for t in texts:
            words = [w for w, _ in Counter(_words(t)).most_common(12)]
            vec = self._unit(words)
            self._passages.append((vec, set(_words(t))))
            out.append(vec)
        return out

    async def embed_query(self, text):
        q_words = set(_words(text))
        own = self._unit(list(q_words))
        hits = [(len(q_words & ws), vec) for vec, ws in self._passages if len(q_words & ws) >= 2]
        if not hits:
            return own
        best = max(h for h, _ in hits)
        near = [vec for h, vec in hits if h >= max(2, best - 0)]
        target = 0.80 if best >= 3 else 0.66
        a = min(0.95, target * math.sqrt(len(near)))
        b = math.sqrt(max(0.0, 1 - a * a))
        mixed = [0.0] * EMBEDDING_DIMENSION
        for vec in near:
            for i, x in enumerate(vec):
                mixed[i] += a * x / math.sqrt(len(near))
        mixed = [m + b * o for m, o in zip(mixed, own)]
        norm = math.sqrt(sum(x * x for x in mixed)) or 1.0
        return [x / norm for x in mixed]

    @property
    def model_name(self):
        return "demo-standin-embedding"

    @property
    def dimension(self):
        return EMBEDDING_DIMENSION
