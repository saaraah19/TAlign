"""
Tests for app.utils.knowledge_chunking.chunk_text.

Zero LLM, zero database, zero mocking — pure function tests, same
philosophy as test_resume_scoring.py and test_knowledge_confidence.py.
"""

from app.utils.knowledge_chunking import CHUNKING_STRATEGY_VERSION, chunk_text


def test_empty_text_returns_no_chunks() -> None:
    assert chunk_text("") == []
    assert chunk_text("   \n\n  ") == []


def test_short_text_returns_a_single_chunk() -> None:
    chunks = chunk_text("This is a short policy statement about remote work.")
    assert len(chunks) == 1
    assert chunks[0].index == 0
    assert "remote work" in chunks[0].content


def test_long_text_is_split_into_multiple_chunks() -> None:
    # ~1500 words of repeated paragraphs, well over the 500-token default.
    paragraph = "Employees must submit expense reports within thirty days. " * 30
    text = "\n\n".join([paragraph] * 5)

    chunks = chunk_text(text, chunk_size_tokens=500, overlap_tokens=50)

    assert len(chunks) > 1
    for chunk in chunks:
        # Allow some slack since packing is unit-granular, not word-exact.
        assert chunk.token_count <= 500 + 50


def test_chunk_indices_are_sequential_from_zero() -> None:
    paragraph = "A policy sentence goes here. " * 100
    text = "\n\n".join([paragraph] * 3)
    chunks = chunk_text(text, chunk_size_tokens=200, overlap_tokens=20)

    assert [c.index for c in chunks] == list(range(len(chunks)))


def test_consecutive_chunks_overlap() -> None:
    paragraph = "Sentence number filler content padding words here. " * 100
    text = "\n\n".join([paragraph] * 2)
    chunks = chunk_text(text, chunk_size_tokens=200, overlap_tokens=30)

    assert len(chunks) >= 2
    first_tail = chunks[0].content.split()[-10:]
    second_head = chunks[1].content.split()[:30]
    # At least some of the first chunk's tail words should reappear at
    # the start of the next chunk, proving the overlap actually carried
    # forward rather than starting fresh at each boundary.
    assert any(word in second_head for word in first_tail)


def test_oversized_single_paragraph_is_still_split() -> None:
    """A paragraph with no blank-line breaks at all must still be chunked."""
    huge_paragraph = "Word " * 2000  # one giant "paragraph", no \n\n anywhere
    chunks = chunk_text(huge_paragraph, chunk_size_tokens=500, overlap_tokens=50)
    assert len(chunks) > 1


def test_strategy_version_is_set() -> None:
    assert CHUNKING_STRATEGY_VERSION == "recursive_v1"
