"""Structured entity extraction from resume sections (heuristic, rule-based)."""

from __future__ import annotations

import re
from datetime import date

from app.document_processing.text_utils import merge_wrapped_lines, split_bullet

_MONTHS = (
    r"(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|"
    r"sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"
)
_DATE_TOKEN = rf"(?:{_MONTHS}\.?\s+)?(?:19|20)\d{{2}}|\d{{1,2}}/(?:19|20)\d{{2}}"
DATE_RANGE_RE = re.compile(
    rf"(?P<start>{_DATE_TOKEN})\s*(?:-|–|—|to|until)\s*"
    rf"(?P<end>{_DATE_TOKEN}|present|current|now|till date|ongoing)",
    re.I,
)
_MONTH_NUM = {
    m: i + 1 for i, m in enumerate(["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"])
}

TITLE_WORDS = re.compile(
    r"\b(?:engineer|developer|intern|trainee|manager|analyst|scientist|lead|architect|consultant|"
    r"designer|administrator|specialist|associate|director|officer|head|technician|researcher|"
    r"assistant|executive|programmer|coordinator|president|founder|co-founder|fellow|apprentice|"
    r"sde|swe|tester|qa|devops|sre)\b",
    re.I,
)
_INSTITUTION_RE = re.compile(r"\b(?:university|institute|college|school|academy|polytechnic|iit|nit|iiit|bits)\b", re.I)
_YEAR_RE = re.compile(r"(?:19|20)\d{2}")
_AMBIGUOUS_DEGREE = r"(?:ME|BE|MA|BA)(?=\s+[A-Z])"
DEGREE_PATTERNS: list[tuple[int, re.Pattern[str]]] = [
    (4, re.compile(r"(?<![A-Za-z])Ph\.?\s?D\.?(?![A-Za-z])|\bdoctorate\b", re.I)),
    (
        3,
        re.compile(
            r"(?<![A-Za-z])(?:MBA|MCA|M\.?\s?Tech|M\.?\s?Sc?\.?|MS|M\.E\.|M\.A\.|"
            + _AMBIGUOUS_DEGREE.replace("ME|BE|MA|BA", "ME|MA")
            + r")(?![A-Za-z])|\b(?i:master(?:'?s)?)\b",
        ),
    ),
    (
        2,
        re.compile(
            r"(?<![A-Za-z])(?:BCA|BBA|B\.?\s?Tech|B\.?\s?Sc?\.?|BS|B\.E\.|B\.A\.|"
            + _AMBIGUOUS_DEGREE.replace("ME|BE|MA|BA", "BE|BA")
            + r")(?![A-Za-z])|\b(?i:bachelor(?:'?s)?)\b",
        ),
    ),
    (1, re.compile(r"\bdiploma\b|\bassociate(?:'s)? degree\b", re.I)),
]
_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_PHONE_RE = re.compile(r"(?<!\d)(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{2,5}\)?[\s.-]?){2,4}\d{2,4}(?!\d)")
_LINK_RE = re.compile(r"(?:https?://|www\.)\S+|\b(?:linkedin|github|gitlab)\.com/\S+", re.I)
_TECH_PREFIX_RE = re.compile(
    r"^\s*(?:tech(?:nologies| stack)?|stack|tools?|environment|built with|technologies used|tools used)\s*[:\-–]\s*",
    re.I,
)


def degree_level(text: str) -> int:
    """Highest degree level mentioned in `text` (0 none, 1 diploma ... 4 doctorate)."""
    for level, pattern in DEGREE_PATTERNS:
        if pattern.search(text):
            return level
    return 0


def _parse_date(token: str, is_end: bool, today: date) -> tuple[int, int]:
    low = token.lower().strip()
    if low in {"present", "current", "now", "till date", "ongoing"}:
        return today.year, today.month
    year_match = _YEAR_RE.search(low)
    slash = re.match(r"(\d{1,2})/((?:19|20)\d{2})", low)
    if slash:
        return int(slash.group(2)), min(max(int(slash.group(1)), 1), 12)
    year = int(year_match.group()) if year_match else today.year
    month_match = re.match(r"[a-z]{3}", low)
    if month_match and month_match.group() in _MONTH_NUM:
        return year, _MONTH_NUM[month_match.group()]
    return year, 12 if is_end else 1


def estimate_years(lines: list[str], today: date | None = None) -> float:
    """Total months covered by (merged) date ranges in `lines`, in years."""
    today = today or date.today()
    spans: list[tuple[int, int]] = []
    for line in lines:
        for match in DATE_RANGE_RE.finditer(line):
            sy, sm = _parse_date(match.group("start"), False, today)
            ey, em = _parse_date(match.group("end"), True, today)
            start, end = sy * 12 + sm, ey * 12 + em
            if end >= start:
                spans.append((start, end))
    spans.sort()
    total, cursor_end = 0, None
    for start, end in spans:
        if cursor_end is None or start > cursor_end:
            total += end - start + 1
            cursor_end = end
        elif end > cursor_end:
            total += end - cursor_end
            cursor_end = end
    return round(total / 12, 1)


def _clean_lines(content: str) -> list[str]:
    return merge_wrapped_lines(content.splitlines())


def parse_contact(first_section_text: str, raw_text: str) -> dict:
    head = "\n".join(raw_text.splitlines()[:12])
    email = _EMAIL_RE.search(raw_text)
    phone = next(
        (m.group().strip() for m in _PHONE_RE.finditer(head) if sum(c.isdigit() for c in m.group()) >= 9),
        None,
    )
    links = list(dict.fromkeys(m.group().rstrip(".,;)") for m in _LINK_RE.finditer(raw_text)))[:5]
    name = None
    for line in first_section_text.splitlines():
        candidate = line.strip()
        if not candidate:
            continue
        words = candidate.split()
        if 1 < len(words) <= 4 and re.fullmatch(r"[A-Za-z][A-Za-z.'\- ]+", candidate):
            name = candidate.title() if candidate.isupper() else candidate
        break
    return {"name": name, "email": email.group() if email else None, "phone": phone, "links": links}


def parse_experience(content: str) -> list[dict]:
    lines = _clean_lines(content)
    parsed = [(split_bullet(line)) for line in lines]  # (text, is_bullet)
    date_idx = [i for i, (t, b) in enumerate(parsed) if not b and DATE_RANGE_RE.search(t)]

    entries: list[dict] = []
    if date_idx:
        starts: list[int] = []
        previous_end = -1
        for i in date_idx:
            start = i
            while start - 1 > previous_end and start - i < 2:
                prev_text, prev_bullet = parsed[start - 1]
                if prev_bullet or DATE_RANGE_RE.search(prev_text) or len(prev_text.split()) > 10:
                    break
                start -= 1
            starts.append(start)
            previous_end = i
        for n, i in enumerate(date_idx):
            end = starts[n + 1] if n + 1 < len(starts) else len(parsed)
            header_text = " | ".join(t for t, _ in parsed[starts[n] : i + 1])
            bullets = [t for t, _ in parsed[i + 1 : end] if t]
            entries.append(_experience_entry(header_text, bullets))
        return entries

    # No dates: treat short non-bullet lines followed by a bullet as entry headers.
    current: dict | None = None
    for idx, (text, is_bullet) in enumerate(parsed):
        if not text:
            continue
        next_is_bullet = idx + 1 < len(parsed) and parsed[idx + 1][1]
        if not is_bullet and len(text.split()) <= 12 and (next_is_bullet or current is None):
            current = _experience_entry(text, [])
            entries.append(current)
        elif current is not None:
            current["bullets"].append(text)
    return entries


def _experience_entry(header: str, bullets: list[str]) -> dict:
    date_match = DATE_RANGE_RE.search(header)
    date_range = date_match.group().strip() if date_match else None
    header_clean = DATE_RANGE_RE.sub("", header).strip(" |,-–—()")
    parts = [p.strip() for p in re.split(r"\s+\|\s+|\s[–—-]\s|,\s+| at | @ ", header_clean) if p.strip()]
    title = next((p for p in parts if TITLE_WORDS.search(p)), None)
    organization = next((p for p in parts if p != title), None)
    if title is None and parts:
        title = parts[0]
        organization = parts[1] if len(parts) > 1 else None
    return {"title": title, "organization": organization, "date_range": date_range, "bullets": bullets}


def parse_education(content: str) -> list[dict]:
    entries: list[dict] = []
    current: dict = {}

    def push() -> None:
        nonlocal current
        if current.get("degree") or current.get("institution"):
            entries.append(
                {
                    "degree": current.get("degree"),
                    "institution": current.get("institution"),
                    "year": current.get("year"),
                }
            )
        current = {}

    for raw in _clean_lines(content):
        text, _ = split_bullet(raw)
        years = _YEAR_RE.findall(text)
        has_degree = degree_level(text) > 0
        has_inst = bool(_INSTITUTION_RE.search(text))
        if has_degree:
            if current.get("degree"):
                push()
            current["degree"] = _YEAR_RE.sub("", text).strip(" ,-–—()|")
        if has_inst:
            if current.get("institution") and not has_degree:
                push()
            segment = next((p.strip() for p in re.split(r",|\s[|–—-]\s", text) if _INSTITUTION_RE.search(p)), text)
            current["institution"] = _YEAR_RE.sub("", segment).strip(" ,-–—()|")
        if years and (has_degree or has_inst):
            current["year"] = years[-1]
    push()
    return entries


def parse_certifications(content: str) -> list[str]:
    items: list[str] = []
    for raw in _clean_lines(content):
        text, _ = split_bullet(raw)
        if 3 <= len(text) <= 160:
            items.append(text)
    return items


def parse_projects(content: str) -> list[dict]:
    projects: list[dict] = []
    current: dict | None = None
    for raw in _clean_lines(content):
        text, is_bullet = split_bullet(raw)
        if not text:
            continue
        tech_match = _TECH_PREFIX_RE.match(text)
        if tech_match:
            if current is None:
                current = {"name": "Project", "tech": [], "bullets": []}
                projects.append(current)
            for token in re.split(r"[,;|/]", text[tech_match.end() :]):
                token = token.strip()
                if token and len(token) <= 40:
                    current["tech"].append(token)
        elif is_bullet:
            if current is None:
                current = {"name": "Project", "tech": [], "bullets": []}
                projects.append(current)
            current["bullets"].append(text)
        else:
            looks_like_header = len(text.split()) <= 16 and not text[0].islower()
            if current is None or (looks_like_header and (current["bullets"] or current["tech"])):
                name = re.split(r"\s+\|\s+|\s[–—-]\s|\s\(", text)[0].strip()
                current = {"name": name or text, "tech": [], "bullets": []}
                projects.append(current)
            else:
                current["bullets"].append(text)
    return projects


def build_parsed_data(sections: dict[str, str], raw_text: str, today: date | None = None) -> dict:
    """`sections` maps section_type -> concatenated content."""
    experience_text = sections.get("experience", "")
    experience = parse_experience(experience_text) if experience_text else []
    education_text = sections.get("education", "")
    if education_text:
        degree_lines = education_text.splitlines()
    else:  # no heading: only trust lines that clearly describe a degree
        degree_lines = [
            ln
            for ln in raw_text.splitlines()
            if _INSTITUTION_RE.search(ln) or re.search(r"\b(?:degree|bachelor|master|doctorate)\b", ln, re.I)
        ]
    levels = [degree_level(split_bullet(ln)[0]) for ln in degree_lines]
    return {
        "contact": parse_contact(sections.get("contact", raw_text), raw_text),
        "experience": experience,
        "education": parse_education(education_text) if education_text else [],
        "certifications": parse_certifications(sections.get("certifications", "")),
        "projects": parse_projects(sections.get("projects", "")),
        "estimated_years_experience": estimate_years(experience_text.splitlines(), today),
        "highest_degree_level": max(levels) if levels else 0,
    }
