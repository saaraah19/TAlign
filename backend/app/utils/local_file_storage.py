"""
Local file storage for resume uploads.

Deterministic, zero LLM, zero DB — pure file I/O. Matches Slice 0's
stated MVP storage decision (local disk; StorageProvider abstraction for
S3/Supabase deferred until a real feature needs it).
"""

import uuid
from pathlib import Path

from app.core.config import settings


def save_resume_file(*, candidate_id: uuid.UUID, filename: str, content: bytes) -> str:
    """
    Writes the uploaded file to
    `{local_storage_path}/resumes/{candidate_id}/{uuid}_{filename}` and
    returns the path. The UUID prefix avoids collisions if the same
    candidate uploads two files with the same name.
    """
    candidate_dir = Path(settings.local_storage_path) / "resumes" / str(candidate_id)
    candidate_dir.mkdir(parents=True, exist_ok=True)

    safe_filename = f"{uuid.uuid4().hex}_{filename}"
    file_path = candidate_dir / safe_filename
    file_path.write_bytes(content)

    return str(file_path)


def read_resume_file(file_path: str) -> bytes:
    return Path(file_path).read_bytes()
