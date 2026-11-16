"""Job description parsing: requirements with importance and evidence from the source text."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.document_processing.resume_entities import DEGREE_PATTERNS, TITLE_WORDS
from app.document_processing.text_utils import split_bullet
from app.nlp.taxonomy import get_taxonomy

IMPORTANCE_RANK = {"required": 3, "preferred": 2, "contextual": 1}
MAX_RESPONSIBILITIES = 15
MAX_UNLISTED_TERMS = 20

_REQ = (
    r"requirements?|qualifications?|what you(?:'ll| will)? need|must[- ]haves?|required skills|"
    r"required qualifications|required experience|minimum qualifications|basic qualifications|"
    r"who you are|your profile|what we(?:'re| are) looking for|you have|you bring|skills|"
    r"skills (?:and|&) experience|key skills|technical skills|about you|what you bring|"
    r"experience required|essential skills|tech stack|our stack|technologies"
)
_PREF = (
    r"preferred(?: qualifications| skills| experience)?|nice[- ]to[- ]haves?|bonus(?: points)?|"
    r"good to have|desired(?: skills)?|a plus|pluses|additional qualifications|plus points|"
    r"extra credit|desirable"
)
_RESP = (
    r"responsibilit(?:y|ies)|what you(?:'ll| will) do|duties|the role|your role|day[- ]to[- ]day|"
    r"in this role|your impact|key responsibilities|role overview|what you(?:'ll| will) be doing|"
    r"job description|about the role|what the job involves"
)
_OTHER = (
    r"about (?:us|the company|the team|[a-z0-9 &.]{2,30})|who we are|benefits|perks|what we offer|"
    r"compensation|why join us|our (?:mission|culture|values)|equal opportunity|how to apply|"
    r"company overview|life at [a-z0-9 ]+|why [a-z0-9 ]+\??"
)
_HEADINGS = [
    ("preferred", re.compile(rf"^(?:{_PREF})$", re.I)),
    ("required", re.compile(rf"^(?:{_REQ})$", re.I)),
    ("responsibilities", re.compile(rf"^(?:{_RESP})$", re.I)),
    ("other", re.compile(rf"^(?:{_OTHER})$", re.I)),
]
_PREFERRED_CUE = re.compile(
    r"\b(?:nice[- ]to[- ]have|preferred|bonus|a plus|is a plus|are a plus|good to have|ideally|"
    r"desirable|advantage|beneficial|would be great|not required|plus)\b",
    re.I,
)
_EXPERIENCE_RE = re.compile(r"(?<![\d.])(\d{1,2})\s*\+?\s*(?:(?:-|–|to)\s*\d{1,2}\s*\+?\s*)?(?:years?|yrs?)\b", re.I)
_EDU_CONTEXT = re.compile(
    r"\b(?:degree|bachelor\w*|master\w*|doctorate|ph\.?d|diploma|b\.tech|btech|m\.tech|mtech|b\.sc|bsc|m\.sc|msc|"
    r"graduat\w+|university|education)\b",
    re.I,
)
_UNLISTED_CUE = re.compile(
    r"(?:experience (?:with|in|using)|knowledge of|proficien\w+ (?:in|with)|familiarity with|"
    r"expertise in|understanding of|background in|hands-on (?:with|experience with)|working with)\s+(.+)",
    re.I,
)
_UNLISTED_TOKEN = re.compile(r"\b(?:[a-z]+[A-Z][A-Za-z0-9]*|[A-Z]{2,}[A-Za-z0-9]*|[A-Za-z]+\d+[A-Za-z0-9]*)\b")
_UNLISTED_STOP = {"AND", "OR", "THE", "US", "UK", "EU", "USA", "CEO", "CTO", "PHD", "BS", "MS", "MBA", "ASAP", "PTO"}
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?;])\s+(?=[A-Z0-9])")
_EDU_NAMES = {1: "Diploma", 2: "Bachelor's degree", 3: "Master's degree", 4: "Doctorate"}


@dataclass
class ParsedRequirement:
    kind: str  # skill | responsibility | experience | education | certification
    canonical_name: str
    surface_form: str
    importance: str
    category: str
    evidence_snippet: str | None = None
    min_years: float | None = None


@dataclass
class ParsedJob:
    title_guess: str | None
    requirements: list[ParsedRequirement] = field(default_factory=list)


def _match_heading(line: str) -> tuple[str, str] | None:
    """Return (section, rest_of_line) when `line` is (or starts with) a section heading."""
    text = re.sub(r"^[#*_\s]+|[*_\s]+$", "", line)
    whole = text.rstrip(":").strip().strip("*_ ")
    if whole and len(whole.split()) <= 8:
        for section, pattern in _HEADINGS:
            if pattern.match(whole):
                return section, ""
    if ":" in text:
        head, _, rest = text.partition(":")
        head = head.strip().strip("*_ ")
        if rest.strip() and head and len(head.split()) <= 8:
            for section, pattern in _HEADINGS:
                if pattern.match(head):
                    return section, rest.strip()
    return None


def _guess_title(lines: list[str]) -> str | None:
    for line in lines[:8]:
        text = re.sub(r"^[#*_\s]+|[*_\s]+$", "", line)
        if 1 < len(text.split()) <= 10 and TITLE_WORDS.search(text) and not re.search(r"[.!?]$", text):
            return text[:120]
    return None


def _importance(sentence: str, section: str, category: str) -> str:
    if category == "soft_skill":
        return "contextual"
    if _PREFERRED_CUE.search(sentence):
        return "preferred"
    if section == "preferred":
        return "preferred"
    if section == "other":
        return "contextual"
    return "required"


def _snippet(text: str) -> str:
    return text if len(text) <= 200 else text[:197] + "..."


def parse_job(text: str) -> ParsedJob:
    taxonomy = get_taxonomy()
    raw_lines = [ln for ln in text.replace("\r", "").split("\n")]
    requirements: dict[tuple[str, str], ParsedRequirement] = {}
    responsibilities: list[ParsedRequirement] = []
    unlisted_count = 0
    section = "required"  # no heading info -> treat content as requirements

    def add(req: ParsedRequirement) -> None:
        key = (req.kind, req.canonical_name.lower())
        existing = requirements.get(key)
        if existing is None or IMPORTANCE_RANK[req.importance] > IMPORTANCE_RANK[existing.importance]:
            requirements[key] = req

    for raw in raw_lines:
        stripped = raw.strip()
        if not stripped:
            continue
        line, _ = split_bullet(stripped)
        heading = _match_heading(line)
        if heading:
            section, line = heading[0], heading[1]
            if not line:
                continue
        sentences = _SENTENCE_SPLIT.split(line) if len(line) > 160 else [line]
        for sentence in (s.strip() for s in sentences):
            if not sentence:
                continue
            found_skills: list[str] = []
            for mention in taxonomy.find(sentence):
                skill = taxonomy.get(mention.canonical)
                category = skill.category if skill else "other"
                kind = "certification" if category == "certification" else "skill"
                found_skills.append(mention.canonical)
                add(
                    ParsedRequirement(
                        kind=kind,
                        canonical_name=mention.canonical,
                        surface_form=mention.surface,
                        importance=_importance(sentence, section, category),
                        category=category,
                        evidence_snippet=_snippet(sentence),
                    )
                )

            unlisted_match = _UNLISTED_CUE.search(sentence)
            if unlisted_match and unlisted_count < MAX_UNLISTED_TERMS:
                for token in _UNLISTED_TOKEN.findall(re.split(r"[.;]", unlisted_match.group(1))[0]):
                    if token.upper() in _UNLISTED_STOP or taxonomy.resolve(token):
                        continue
                    key = ("skill", token.lower())
                    if key not in requirements and unlisted_count < MAX_UNLISTED_TERMS:
                        unlisted_count += 1
                        add(
                            ParsedRequirement(
                                kind="skill",
                                canonical_name=token,
                                surface_form=token,
                                importance=_importance(sentence, section, "other"),
                                category="other",
                                evidence_snippet=_snippet(sentence),
                            )
                        )

            if re.search(r"experience|exp\b", sentence, re.I):
                for match in _EXPERIENCE_RE.finditer(sentence):
                    years = float(match.group(1))
                    if years > 30 or re.search(r"years? old", sentence, re.I):
                        continue
                    name = f"{match.group(1)}+ years of experience"
                    if found_skills:
                        name += " with " + ", ".join(found_skills[:3])
                    add(
                        ParsedRequirement(
                            kind="experience",
                            canonical_name=name,
                            surface_form=match.group(0),
                            importance=_importance(sentence, section, "other"),
                            category="experience",
                            evidence_snippet=_snippet(sentence),
                            min_years=years,
                        )
                    )

            if _EDU_CONTEXT.search(sentence):
                levels = [lvl for lvl, pattern in DEGREE_PATTERNS if pattern.search(sentence)]
                if levels:
                    level = min(levels)
                    add(
                        ParsedRequirement(
                            kind="education",
                            canonical_name=_EDU_NAMES[level],
                            surface_form=_EDU_NAMES[level],
                            importance=_importance(sentence, section, "other"),
                            category="education",
                            evidence_snippet=_snippet(sentence),
                        )
                    )

            if (
                section == "responsibilities"
                and len(responsibilities) < MAX_RESPONSIBILITIES
                and len(sentence.split()) >= 6
            ):
                responsibilities.append(
                    ParsedRequirement(
                        kind="responsibility",
                        canonical_name=sentence[:240],
                        surface_form=sentence[:240],
                        importance="required",
                        category="responsibility",
                        evidence_snippet=_snippet(sentence),
                    )
                )

    ordered = sorted(requirements.values(), key=lambda r: (-IMPORTANCE_RANK[r.importance], r.kind))
    return ParsedJob(title_guess=_guess_title(raw_lines), requirements=[*ordered, *responsibilities][:140])


def years_required(requirements: list[ParsedRequirement]) -> float | None:
    """Overall minimum experience: the largest general (non skill-specific) requirement."""
    general = [r.min_years for r in requirements if r.kind == "experience" and " with " not in r.canonical_name]
    specific = [r.min_years for r in requirements if r.kind == "experience" and " with " in r.canonical_name]
    pool = [y for y in general if y is not None] or [y for y in specific if y is not None]
    if not pool:
        return None
    return max(pool) if general else min(pool)
