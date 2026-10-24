"""
Content safety guardrail test for the Knowledge Agent — structural, not
a convention. Mirrors tests/test_email_content_safety.py's philosophy:
verify against the actual function signature that nothing beyond
`question` and `chunks` can reach the prompt builder, rather than just
documenting that it shouldn't. A wider signature (e.g. accepting
`company_id`, a user object, or the full document list) would be a
regression even if the current implementation never misuses it — the
guarantee this test protects is "physically cannot", not "currently
doesn't".
"""

import inspect

from app.agents.knowledge.prompts import build_knowledge_answer_prompt


def test_knowledge_answer_prompt_builder_signature_is_minimal() -> None:
    params = set(inspect.signature(build_knowledge_answer_prompt).parameters)
    assert params == {"question", "chunks"}
