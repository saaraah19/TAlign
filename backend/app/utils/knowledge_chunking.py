"""
Knowledge document chunking — plain text -> overlapping chunks.

Entirely deterministic, zero LLM calls, zero network dependency — same
"testable in complete isolation" philosophy as document_text_extraction.py
and app/agents/resume_intelligence/scoring.py. This is the piece most
likely to need tuning once real HR documents are tested against it, which
is exactly why it's kept as a small, pure, fully-unit-tested function
rather than buried inside a service.

Hand-rolled rather than using a text-splitting library (e.g. LangChain's
RecursiveCharacterTextSplitter): `langchain` in this project's
pyproject.toml is pinned as `>=0.3.0` with no upper bound, and the
installed version resolved to 1.3.x — a much newer major version than
existed when that pin was written, in which the text-splitter classes
have moved to a separate `langchain-text-splitters` package not
currently a dependency here. Rather than add a new dependency whose API
surface hasn't been verified against a library that's clearly still
moving, this implements the same "paragraph, then sentence, then word"
recursive-fallback splitting strategy directly — about 60 lines,
fully testable with zero mocking.

--- Methodology ---

Splits on paragraph boundaries (blank lines) first. Any paragraph that
alone exceeds CHUNK_SIZE_TOKENS is further split on sentence boundaries,
and any single "sentence" still too long is split on whitespace as a
last resort — this ordering means a chunk boundary lands on the most
natural break available, only falling back to a cruder cut when the
text genuinely has no better option (e.g. a huge run-on legal clause).

Consecutive chunks overlap by CHUNK_OVERLAP_TOKENS so that content near
a chunk boundary isn't only ever visible from one side of it — a
citation or a retrieval match right at a boundary shouldn't lose
context just because of where the cut happened to fall.

Token counting uses a simple whitespace-word approximation, not a real
tokenizer (e.g. tiktoken) — sizes below are written in that unit and
are approximate, not exact LLM-token counts. Precise enough to make
chunk sizes consistent and testable; getting an exact token count would
require adding a tokenizer dependency for a precision this MVP doesn't
need. Flagged here rather than silently assumed.

CHUNKING_STRATEGY_VERSION: bump if this algorithm changes meaningfully
— persisted as part of KnowledgeDocument.embedding_version (see that
model's docstring), since a chunking change effectively invalidates a
document's existing chunks the same way an embedding model change does.
"""

import re
from dataclasses import dataclass

CHUNKING_STRATEGY_VERSION = "recursive_v1"

CHUNK_SIZE_TOKENS = 500
CHUNK_OVERLAP_TOKENS = 50

_PARAGRAPH_SPLIT = re.compile(r"\n\s*\n")
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")


@dataclass(frozen=True)
class TextChunk:
    index: int
    content: str
    token_count: int


def _word_count(text: str) -> int:
    return len(text.split())


def _split_oversized_unit(unit: str, max_tokens: int) -> list[str]:
    """Sentence-split a paragraph, then word-split any sentence still too long."""
    sentences = [s for s in _SENTENCE_SPLIT.split(unit) if s.strip()]
    pieces: list[str] = []
    for sentence in sentences:
        if _word_count(sentence) <= max_tokens:
            pieces.append(sentence)
            continue
        words = sentence.split()
        for i in range(0, len(words), max_tokens):
            pieces.append(" ".join(words[i : i + max_tokens]))
    return pieces


def chunk_text(
    text: str,
    *,
    chunk_size_tokens: int = CHUNK_SIZE_TOKENS,
    overlap_tokens: int = CHUNK_OVERLAP_TOKENS,
) -> list[TextChunk]:
    """
    Returns an empty list for blank/whitespace-only input — callers
    (KnowledgeDocumentService) treat zero chunks as a processing failure
    for that document, same as a text-extraction failure.
    """
    if not text.strip():
        return []

    paragraphs = [p.strip() for p in _PARAGRAPH_SPLIT.split(text) if p.strip()]

    # Break any paragraph exceeding chunk_size on its own into smaller
    # units first, so the greedy pack step below never has to split a
    # unit mid-assembly.
    units: list[str] = []
    for paragraph in paragraphs:
        if _word_count(paragraph) <= chunk_size_tokens:
            units.append(paragraph)
        else:
            units.extend(_split_oversized_unit(paragraph, chunk_size_tokens))

    # Greedily pack units into chunks up to chunk_size_tokens, carrying
    # the tail of each chunk forward as the start of the next (overlap).
    chunks: list[TextChunk] = []
    current_words: list[str] = []

    def _flush() -> None:
        if current_words:
            content = " ".join(current_words)
            chunks.append(
                TextChunk(index=len(chunks), content=content, token_count=len(current_words))
            )

    for unit in units:
        unit_words = unit.split()
        if current_words and len(current_words) + len(unit_words) > chunk_size_tokens:
            _flush()
            # Carry the overlap tail forward as the start of the next chunk.
            current_words = current_words[-overlap_tokens:] if overlap_tokens else []
        current_words.extend(unit_words)

    _flush()
    return chunks
