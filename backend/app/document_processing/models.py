"""Plain data containers shared by the document parsers. No framework imports."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Line:
    """One visual line of a document, in reading order."""

    text: str
    page: int = 1
    size: float = 0.0
    bold: bool = False
    heading_style: bool = False


@dataclass
class ParsedDocument:
    lines: list[Line]
    page_count: int
    method: str  # pymupdf | pypdf | ocr | docx | text
    extraction_confidence: float
    warnings: list[str] = field(default_factory=list)
    needs_ocr: bool = False

    @property
    def raw_text(self) -> str:
        return "\n".join(line.text for line in self.lines)


@dataclass
class DetectedSection:
    section_type: str
    heading_text: str | None
    content: str
    order_index: int
    page_start: int | None
    confidence: float


class DocumentParseError(Exception):
    """Raised when a document cannot be read at all."""
