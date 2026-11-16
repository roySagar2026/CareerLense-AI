"""Upload validation: extension, size, magic bytes and zip-bomb guard."""

from __future__ import annotations

import io
import os
import re
import zipfile

from app.core.errors import AppError

ALLOWED_TYPES = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
_MAX_UNCOMPRESSED = 60 * 1024 * 1024


def safe_filename(name: str | None) -> str:
    """Display-only filename: no path components, no control characters. Never used as a storage path."""
    base = os.path.basename((name or "resume").replace("\\", "/"))
    base = re.sub(r"[\x00-\x1f\x7f]", "", base).strip()
    return (base or "resume")[:200]


def validate_upload(filename: str | None, data: bytes, max_bytes: int) -> tuple[str, str]:
    """Return (extension, mime) or raise AppError. Content is checked, not just the extension."""
    if not data:
        raise AppError(422, "validation_error", "The uploaded file is empty.")
    if len(data) > max_bytes:
        raise AppError(413, "file_too_large", f"File is larger than {max_bytes // (1024 * 1024)} MB.")
    ext = os.path.splitext(safe_filename(filename))[1].lower()
    if ext not in ALLOWED_TYPES:
        raise AppError(415, "unsupported_file_type", "Only PDF and DOCX resumes are supported.")
    if ext == ".pdf":
        if not data.lstrip()[:5] == b"%PDF-":
            raise AppError(415, "unsupported_file_type", "This file is not a valid PDF.")
    else:
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                names = set(archive.namelist())
                if "word/document.xml" not in names:
                    raise AppError(415, "unsupported_file_type", "This file is not a valid DOCX document.")
                if sum(info.file_size for info in archive.infolist()) > _MAX_UNCOMPRESSED:
                    raise AppError(415, "unsupported_file_type", "This DOCX expands to an unsafe size.")
        except zipfile.BadZipFile as exc:
            raise AppError(415, "unsupported_file_type", "This file is not a valid DOCX document.") from exc
    return ext, ALLOWED_TYPES[ext]
