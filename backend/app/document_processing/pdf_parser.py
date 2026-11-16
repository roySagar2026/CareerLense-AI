"""PDF extraction.

Primary engine: PyMuPDF (font size/bold per line). Fallback: pypdf. Both adapters
produce `Block` objects that go through the same reading-order logic, which handles
two-column layouts. Scanned PDFs are detected by character density; an optional OCR
path (PyMuPDF + Tesseract) runs only when enabled.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.document_processing.models import DocumentParseError, Line, ParsedDocument
from app.document_processing.text_utils import normalize_line

MAX_PAGES = 12
MIN_CHARS_PER_PAGE = 80


@dataclass
class Block:
    x0: float
    y0: float  # top-down coordinate (0 = top of page)
    x1: float
    text: str
    size: float
    bold: bool
    page: int


def order_blocks(blocks: list[Block], page_width: float) -> list[Block]:
    """Return blocks of ONE page in reading order (handles two columns)."""
    if not blocks:
        return []
    width = page_width or max(b.x1 for b in blocks) or 1.0
    spanning = [b for b in blocks if b.x0 < 0.38 * width and b.x1 > 0.62 * width]
    rest = [b for b in blocks if b not in spanning]
    left = [b for b in rest if b.x1 <= 0.56 * width]
    right = [b for b in rest if b.x0 >= 0.44 * width]
    two_column = len(left) >= 4 and len(right) >= 4 and len(left) + len(right) >= 0.8 * len(rest)

    if not two_column:
        return sorted(blocks, key=lambda b: (round(b.y0 / 3), b.x0))

    spanning.sort(key=lambda b: b.y0)
    zones: list[list[Block]] = [[] for _ in range(len(spanning) + 1)]
    for block in rest:
        zone = sum(1 for s in spanning if s.y0 <= block.y0)
        zones[zone].append(block)

    ordered: list[Block] = []
    for index, zone_blocks in enumerate(zones):
        mid = 0.5 * width
        col_left = sorted((b for b in zone_blocks if b.x0 < mid), key=lambda b: (b.y0, b.x0))
        col_right = sorted((b for b in zone_blocks if b.x0 >= mid), key=lambda b: (b.y0, b.x0))
        ordered.extend(col_left + col_right)
        if index < len(spanning):
            ordered.append(spanning[index])
    return ordered


def _to_document(
    pages: list[tuple[float, list[Block]]], method: str, warnings: list[str], truncated: bool
) -> ParsedDocument:
    lines: list[Line] = []
    for page_width, blocks in pages:
        for block in order_blocks(blocks, page_width):
            text = normalize_line(block.text)
            if text:
                lines.append(Line(text=text, page=block.page, size=block.size, bold=block.bold))
    chars = sum(len(ln.text) for ln in lines)
    page_count = len(pages)
    needs_ocr = page_count > 0 and chars / page_count < MIN_CHARS_PER_PAGE
    if truncated:
        warnings.append(f"Only the first {MAX_PAGES} pages were processed.")
    if needs_ocr:
        warnings.append(
            "This PDF looks scanned (almost no selectable text). Upload a text-based PDF or DOCX, "
            "or enable OCR on the server."
        )
        confidence = 0.15
    else:
        confidence = 0.9 if method == "pymupdf" else 0.8
    return ParsedDocument(
        lines=lines,
        page_count=page_count,
        method=method,
        extraction_confidence=confidence,
        warnings=warnings,
        needs_ocr=needs_ocr,
    )


def _parse_with_pymupdf(data: bytes, ocr_enabled: bool) -> ParsedDocument:
    import fitz  # PyMuPDF

    try:
        doc = fitz.open(stream=data, filetype="pdf")
    except Exception as exc:
        raise DocumentParseError("The PDF file is corrupt or not a valid PDF.") from exc
    if doc.needs_pass:
        raise DocumentParseError("The PDF is password protected. Remove the password and re-upload.")

    warnings: list[str] = []
    pages: list[tuple[float, list[Block]]] = []
    total_pages = doc.page_count
    ocr_used = False
    for index in range(min(total_pages, MAX_PAGES)):
        page = doc[index]
        blocks = _pymupdf_blocks(page, index + 1, None)
        if ocr_enabled and sum(len(b.text) for b in blocks) < MIN_CHARS_PER_PAGE:
            try:
                textpage = page.get_textpage_ocr(flags=0, full=True)
                blocks = _pymupdf_blocks(page, index + 1, textpage)
                ocr_used = True
            except Exception:  # Tesseract missing or failed
                warnings.append("OCR was requested but Tesseract is not available on the server.")
        pages.append((float(page.rect.width), blocks))
    parsed = _to_document(pages, "ocr" if ocr_used else "pymupdf", warnings, total_pages > MAX_PAGES)
    if ocr_used and not parsed.needs_ocr:
        parsed.extraction_confidence = 0.6  # OCR text is inherently less reliable
        parsed.warnings.append("Text was recovered with OCR and may contain errors; review the sections.")
    return parsed


def _pymupdf_blocks(page, page_number: int, textpage) -> list[Block]:
    kwargs = {"textpage": textpage} if textpage is not None else {}
    data = page.get_text("dict", **kwargs)
    blocks: list[Block] = []
    for block in data.get("blocks", []):
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            spans = [s for s in line.get("spans", []) if s.get("text", "").strip()]
            if not spans:
                continue
            x0, y0, x1, _ = line["bbox"]
            blocks.append(
                Block(
                    x0=x0,
                    y0=y0,
                    x1=x1,
                    text="".join(s["text"] for s in spans),
                    size=max(float(s.get("size", 0)) for s in spans),
                    bold=all((s.get("flags", 0) & 16) or "bold" in str(s.get("font", "")).lower() for s in spans),
                    page=page_number,
                )
            )
    return blocks


def _parse_with_pypdf(data: bytes) -> ParsedDocument:
    import io

    from pypdf import PdfReader
    from pypdf.errors import PdfReadError

    try:
        reader = PdfReader(io.BytesIO(data))
    except (PdfReadError, ValueError, OSError) as exc:
        raise DocumentParseError("The PDF file is corrupt or not a valid PDF.") from exc
    if reader.is_encrypted:
        raise DocumentParseError("The PDF is password protected. Remove the password and re-upload.")

    pages: list[tuple[float, list[Block]]] = []
    total_pages = len(reader.pages)
    for index in range(min(total_pages, MAX_PAGES)):
        page = reader.pages[index]
        height = float(page.mediabox.height)
        width = float(page.mediabox.width)
        fragments: list[tuple[float, float, str, float, bool]] = []

        def visitor(text, cm, tm, font_dict, font_size, _acc=fragments):
            if not text or not text.strip():
                return
            x = tm[4] * cm[0] + cm[4]
            y = tm[5] * cm[3] + cm[5]
            base = str((font_dict or {}).get("/BaseFont", "")).lower()
            _acc.append((x, y, text.replace("\n", " "), float(font_size or 0), "bold" in base))

        try:
            page.extract_text(visitor_text=visitor)
        except Exception as exc:
            raise DocumentParseError("The PDF text could not be extracted.") from exc

        grouped: dict[int, list[tuple[float, float, str, float, bool]]] = {}
        for frag in fragments:
            grouped.setdefault(round(frag[1] / 2), []).append(frag)
        blocks: list[Block] = []
        for _, frags in grouped.items():
            frags.sort(key=lambda f: f[0])
            blocks.append(
                Block(
                    x0=frags[0][0],
                    y0=height - frags[0][1],
                    x1=frags[-1][0] + 5.0 * len(frags[-1][2]),
                    text=" ".join(f[2].strip() for f in frags),
                    size=max(f[3] for f in frags),
                    bold=all(f[4] for f in frags),
                    page=index + 1,
                )
            )
        pages.append((width, blocks))
    return _to_document(pages, "pypdf", [], total_pages > MAX_PAGES)


def parse_pdf(data: bytes, ocr_enabled: bool = False) -> ParsedDocument:
    try:
        import fitz  # noqa: F401
    except ImportError:
        return _parse_with_pypdf(data)
    return _parse_with_pymupdf(data, ocr_enabled)
