"""Rule-based resume section detection with per-section confidence."""

from __future__ import annotations

import re
import statistics

from app.document_processing.models import DetectedSection, Line

# Exact heading phrases (normalised) -> section type.
HEADING_PHRASES: dict[str, str] = {}
for _type, _phrases in {
    "summary": [
        "summary",
        "professional summary",
        "career summary",
        "executive summary",
        "profile",
        "professional profile",
        "personal profile",
        "objective",
        "career objective",
        "about me",
        "about",
        "overview",
        "summary of qualifications",
    ],
    "skills": [
        "skills",
        "technical skills",
        "core skills",
        "key skills",
        "core competencies",
        "competencies",
        "technologies",
        "tech stack",
        "technical proficiencies",
        "skills and tools",
        "tools and technologies",
        "technical expertise",
        "areas of expertise",
        "skills summary",
    ],
    "experience": [
        "experience",
        "work experience",
        "professional experience",
        "employment history",
        "work history",
        "employment",
        "career history",
        "relevant experience",
        "internships",
        "internship experience",
        "industry experience",
        "internship",
    ],
    "projects": [
        "projects",
        "personal projects",
        "academic projects",
        "key projects",
        "selected projects",
        "project experience",
        "side projects",
        "technical projects",
        "notable projects",
    ],
    "education": [
        "education",
        "academic background",
        "academic qualifications",
        "education and training",
        "educational qualifications",
        "academics",
        "qualifications",
        "academic profile",
    ],
    "certifications": [
        "certifications",
        "certificates",
        "licenses and certifications",
        "certifications and courses",
        "courses",
        "training",
        "professional certifications",
        "licenses",
        "courses and certifications",
    ],
    "achievements": [
        "achievements",
        "awards",
        "honors",
        "honours",
        "accomplishments",
        "awards and honors",
        "achievements and awards",
        "key achievements",
        "awards and achievements",
    ],
    "other": [
        "publications",
        "languages",
        "interests",
        "hobbies",
        "volunteer experience",
        "volunteering",
        "references",
        "extracurricular activities",
        "activities",
        "positions of responsibility",
        "leadership",
        "patents",
        "additional information",
        "personal details",
    ],
}.items():
    for _p in _phrases:
        HEADING_PHRASES[_p] = _type

_ANCHORS = {
    "skills": "skills",
    "technologies": "skills",
    "competencies": "skills",
    "experience": "experience",
    "employment": "experience",
    "projects": "projects",
    "education": "education",
    "certifications": "certifications",
    "certificates": "certifications",
    "achievements": "achievements",
    "awards": "achievements",
    "summary": "summary",
}
_MODIFIERS = {
    "and",
    "of",
    "the",
    "technical",
    "professional",
    "key",
    "core",
    "relevant",
    "additional",
    "academic",
    "work",
    "industry",
    "tools",
    "other",
    "selected",
    "personal",
    "software",
}


def _norm_heading(text: str) -> str:
    text = text.lower().replace("&", " and ")
    text = re.sub(r"[^a-z ]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def classify_heading(line: Line, body_size: float = 0.0) -> tuple[str, float] | None:
    """Return (section_type, confidence) when the line looks like a section heading."""
    raw = line.text.strip()
    if not raw or raw.endswith((".", ",", ";")) or any(ch.isdigit() for ch in raw):
        return None
    norm = _norm_heading(raw)
    words = norm.split()
    if not 1 <= len(words) <= 6:
        return None
    formatted = (
        line.heading_style
        or line.bold
        or raw.isupper()
        or raw.istitle()
        or (body_size > 0 and line.size >= body_size * 1.12)
    )
    if norm in HEADING_PHRASES:
        return HEADING_PHRASES[norm], 0.95 if formatted else 0.8
    anchors = [w for w in words if w in _ANCHORS]
    if anchors and formatted and all(w in _ANCHORS or w in _MODIFIERS for w in words):
        return _ANCHORS[anchors[0]], 0.75
    return None


def detect_sections(lines: list[Line]) -> list[DetectedSection]:
    """Split document lines into typed sections. Text before the first heading is `contact`."""
    sizes = [ln.size for ln in lines if ln.size > 0]
    body_size = statistics.median(sizes) if sizes else 0.0

    sections: list[DetectedSection] = []
    current_type, current_heading = "contact", None
    current_conf, current_page = 0.6, lines[0].page if lines else 1
    buffer: list[str] = []

    def flush() -> None:
        content = "\n".join(buffer).strip()
        if content or current_heading:
            sections.append(
                DetectedSection(
                    section_type=current_type,
                    heading_text=current_heading,
                    content=content,
                    order_index=len(sections),
                    page_start=current_page,
                    confidence=current_conf,
                )
            )

    for line in lines:
        hit = classify_heading(line, body_size)
        if hit:
            flush()
            buffer = []
            current_type, current_conf = hit
            current_heading, current_page = line.text.strip(), line.page
        else:
            buffer.append(line.text)
    flush()

    # A document with no recognised headings: keep one low-confidence section.
    if len(sections) == 1 and sections[0].section_type == "contact" and len(lines) > 8:
        sections[0] = DetectedSection(
            section_type="other",
            heading_text=None,
            content=sections[0].content,
            order_index=0,
            page_start=sections[0].page_start,
            confidence=0.3,
        )
    return sections


def structure_confidence(sections: list[DetectedSection]) -> float:
    """0..1 confidence that the section structure was recovered."""
    real = [s for s in sections if s.heading_text]
    if not real:
        return 0.3
    key = {s.section_type for s in real} & {"skills", "experience", "projects", "education"}
    base = sum(s.confidence for s in real) / len(real)
    return round(min(1.0, base * (0.6 + 0.1 * min(len(key), 4))), 2)
