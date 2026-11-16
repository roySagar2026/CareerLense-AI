from __future__ import annotations

import pytest

from app.document_processing.models import DocumentParseError
from app.document_processing.pdf_parser import Block, _parse_with_pypdf, order_blocks
from app.document_processing.section_detector import detect_sections
from tests.synthetic import make_pdf


def _block(x0, y0, text, width=200, page=1):
    return Block(x0=x0, y0=y0, x1=x0 + width, text=text, size=10, bold=False, page=page)


def test_two_column_reading_order():
    left = [_block(40, 100 + i * 20, f"L{i}", 180) for i in range(5)]
    right = [_block(330, 100 + i * 20, f"R{i}", 180) for i in range(5)]
    header = Block(x0=40, y0=50, x1=560, text="HEADER", size=14, bold=True, page=1)
    ordered = [b.text for b in order_blocks(left + right + [header], 600)]
    assert ordered == ["HEADER", "L0", "L1", "L2", "L3", "L4", "R0", "R1", "R2", "R3", "R4"]


def test_single_column_order_is_top_down():
    blocks = [_block(50, 300, "c"), _block(50, 100, "a"), _block(50, 200, "b")]
    assert [b.text for b in order_blocks(blocks, 600)] == ["a", "b", "c"]


def test_pypdf_extracts_and_sections():
    pytest.importorskip("pypdf")
    pytest.importorskip("reportlab")
    doc = _parse_with_pypdf(make_pdf())
    assert doc.method == "pypdf" and not doc.needs_ocr
    assert "Asha Verma" in doc.raw_text
    types = {s.section_type for s in detect_sections(doc.lines)}
    assert {"skills", "experience", "education"} <= types


def test_garbage_pdf_raises():
    pytest.importorskip("pypdf")
    with pytest.raises(DocumentParseError):
        _parse_with_pypdf(b"%PDF-1.4 this is not really a pdf")
