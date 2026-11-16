"""DOCX extraction with python-docx: paragraphs and tables in document order."""

from __future__ import annotations

import io

from app.document_processing.models import DocumentParseError, Line, ParsedDocument
from app.document_processing.text_utils import normalize_line

_P_TAG = "}p"
_TBL_TAG = "}tbl"


def _paragraph_line(paragraph) -> Line | None:
    text = normalize_line(paragraph.text)
    if not text:
        return None
    style = (paragraph.style.name or "") if paragraph.style is not None else ""
    runs = [r for r in paragraph.runs if r.text.strip()]
    bold = bool(runs) and all(bool(r.bold) for r in runs)
    size = 0.0
    for run in runs:
        if run.font.size:
            size = max(size, float(run.font.size.pt))
    is_list = "list" in style.lower() or (paragraph._p.pPr is not None and paragraph._p.pPr.numPr is not None)
    if is_list and not text.startswith(("•", "-", "–")):
        text = f"• {text}"
    return Line(
        text=text,
        page=1,
        size=size,
        bold=bold,
        heading_style=style.lower().startswith(("heading", "title")),
    )


def parse_docx(data: bytes) -> ParsedDocument:
    try:
        from docx import Document
        from docx.table import Table
        from docx.text.paragraph import Paragraph
    except ImportError as exc:  # pragma: no cover - dependency missing
        raise DocumentParseError("python-docx is not installed") from exc

    try:
        document = Document(io.BytesIO(data))
    except Exception as exc:
        raise DocumentParseError("The DOCX file is corrupt or not a valid Word document.") from exc

    lines: list[Line] = []
    for child in document.element.body.iterchildren():
        tag = child.tag
        if tag.endswith(_P_TAG):
            line = _paragraph_line(Paragraph(child, document))
            if line:
                lines.append(line)
        elif tag.endswith(_TBL_TAG):
            table = Table(child, document)
            for row in table.rows:
                cells: list[str] = []
                for cell in row.cells:
                    cell_text = normalize_line(" ".join(p.text for p in cell.paragraphs))
                    if cell_text and cell_text not in cells:  # merged cells repeat
                        cells.append(cell_text)
                if cells:
                    lines.append(Line(text=" | ".join(cells), page=1))

    warnings: list[str] = []
    chars = sum(len(ln.text) for ln in lines)
    if chars < 150:
        warnings.append("Very little text was found in this DOCX; text boxes and images are not read.")
        confidence = 0.35
    else:
        confidence = 0.95
    return ParsedDocument(lines=lines, page_count=1, method="docx", extraction_confidence=confidence, warnings=warnings)
