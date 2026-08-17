"""
Document text extraction — file bytes -> plain text.

Entirely deterministic (pypdf / python-docx / plain decode). Originally
written for Resume Intelligence (this is the step BEFORE any LLM
involvement — see app/models/resume.py's docstring for that pipeline
shape); renamed from resume_text_extraction.py in Slice 6 once the
Knowledge Agent needed the exact same file-bytes-to-text operation for
uploaded policy documents. Nothing in this file's implementation was
ever resume-specific — it's a generic document utility that happened to
have only one caller until now.

Raises ResumeTextExtractionError on failure (corrupt file, unreadable
PDF, etc) — the name predates this file's generalization and is kept
as-is rather than renamed, since renaming an exception type ripples
through every catch site across two now-unrelated domains for a purely
cosmetic gain; not worth the churn.
"""

from app.core.exceptions import ResumeTextExtractionError

SUPPORTED_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
}


def extract_text(*, content_type: str, content: bytes) -> str:
    if content_type == "application/pdf":
        return _extract_pdf_text(content)
    if content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return _extract_docx_text(content)
    if content_type == "text/plain":
        return _extract_plain_text(content)
    raise ResumeTextExtractionError(
        f"Unsupported content type for text extraction: {content_type}"
    )


def _extract_pdf_text(content: bytes) -> str:
    try:
        import io

        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(content))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception as exc:  # noqa: BLE001 — any pypdf failure means "we can't read this PDF"
        raise ResumeTextExtractionError(f"Could not extract text from PDF: {exc}") from exc

    if not text.strip():
        raise ResumeTextExtractionError(
            "No extractable text found in this PDF (it may be a scanned image — "
            "OCR is not supported in this version)."
        )
    return text


def _extract_docx_text(content: bytes) -> str:
    try:
        import io

        import docx

        document = docx.Document(io.BytesIO(content))
        text = "\n".join(paragraph.text for paragraph in document.paragraphs)
    except Exception as exc:  # noqa: BLE001
        raise ResumeTextExtractionError(f"Could not extract text from DOCX: {exc}") from exc

    if not text.strip():
        raise ResumeTextExtractionError("No extractable text found in this document.")
    return text


def _extract_plain_text(content: bytes) -> str:
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ResumeTextExtractionError(f"Could not decode text file: {exc}") from exc

    if not text.strip():
        raise ResumeTextExtractionError("The uploaded text file is empty.")
    return text
