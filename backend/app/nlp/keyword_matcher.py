"""Hybrid matching of job requirements against a resume profile.

Tiers (strongest first): exact -> implied -> fuzzy -> semantic (related, never verified) -> missing.
Credit always depends on the *evidence level* of the resume mention, never on how often a
keyword is repeated.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.nlp.extractor import ResumeProfile, SkillEvidence
from app.nlp.job_parser import ParsedRequirement
from app.nlp.semantic_matcher import SemanticMatcher, get_semantic_matcher
from app.nlp.skill_classifier import EVIDENCE_CREDIT, EVIDENCE_RANK, classify_evidence
from app.nlp.taxonomy import get_taxonomy

try:  # RapidFuzz is optional at import time; difflib is the pure-Python fallback.
    from rapidfuzz import fuzz as _fuzz

    def _ratio(a: str, b: str) -> float:
        return float(_fuzz.ratio(a, b))

except ImportError:  # pragma: no cover - exercised when rapidfuzz is absent
    from difflib import SequenceMatcher

    def _ratio(a: str, b: str) -> float:
        return SequenceMatcher(None, a, b).ratio() * 100


FUZZY_THRESHOLD = 90.0
SEMANTIC_CAP = 0.4
RESPONSIBILITY_SECTIONS = {"experience", "projects", "summary"}
_EDU_LEVEL = {"Diploma": 1, "Bachelor's degree": 2, "Master's degree": 3, "Doctorate": 4}
_TERM_TOKEN = re.compile(r"[a-z0-9][a-z0-9+#.]*")


@dataclass
class MatchResult:
    requirement: ParsedRequirement
    match_type: str  # exact | implied | fuzzy | semantic | partial | missing
    result_category: str
    similarity: float
    confidence: float
    credit: float
    occurrences: int
    evidence_level: str | None
    source_section: str | None
    explanation: str
    suggested_section: str | None = None


def _categorize(req: ParsedRequirement, match_type: str, level: str | None) -> str:
    if req.kind == "responsibility":
        return "semantic" if match_type == "semantic" else "contextual"
    if match_type == "exact":
        return "partial" if level == "mentioned" else "exact"
    if match_type in {"implied", "fuzzy", "partial"}:
        return "partial"
    if match_type == "semantic":
        return "semantic"
    if req.importance == "required":
        return "missing_mandatory"
    return "missing_preferred" if req.importance == "preferred" else "contextual"


def _where(evidence: SkillEvidence) -> str:
    return f"in your {evidence.section_type or 'resume'} section"


def _resume_terms(profile: ResumeProfile) -> set[str]:
    tokens = _TERM_TOKEN.findall(profile.raw_text.lower())
    terms: set[str] = set()
    for n in (1, 2, 3):
        for i in range(len(tokens) - n + 1):
            term = " ".join(tokens[i : i + n])
            if 4 <= len(term) <= 30:
                terms.add(term)
    return terms


def _term_evidence(profile: ResumeProfile, term: str) -> SkillEvidence | None:
    """Evidence for a non-taxonomy term found literally in the resume."""
    pattern = re.compile(rf"(?<![A-Za-z0-9_]){re.escape(term)}(?![A-Za-z0-9_])", re.I)
    best: SkillEvidence | None = None
    count = 0
    for unit in profile.units:
        if unit.section_type == "contact" or not pattern.search(unit.text):
            continue
        count += 1
        level = classify_evidence(unit.text, unit.section_type, unit.is_bullet)
        if best is None or EVIDENCE_RANK[level] > EVIDENCE_RANK[best.evidence_level]:
            best = SkillEvidence(term, term, "other", level, unit.section_type, unit.text[:180])
    if best:
        best.occurrences = count
    return best


def _exact(req: ParsedRequirement, ev: SkillEvidence) -> MatchResult:
    level = ev.evidence_level
    confidence = {"demonstrated": 0.95, "listed": 0.8, "mentioned": 0.5}[level]
    note = {
        "demonstrated": "used in described work",
        "listed": "claimed in a skills list or summary",
        "mentioned": "only mentioned in passing, so it earns reduced credit",
    }[level]
    return MatchResult(
        requirement=req,
        match_type="exact",
        result_category=_categorize(req, "exact", level),
        similarity=1.0,
        confidence=confidence,
        credit=EVIDENCE_CREDIT[level],
        occurrences=ev.occurrences,
        evidence_level=level,
        source_section=ev.section_type,
        explanation=f"Found '{ev.surface_form}' {_where(ev)} ({level}: {note}). Evidence: \"{ev.snippet}\"",
    )


def _match_skill(
    req: ParsedRequirement, profile: ResumeProfile, terms: set[str] | None, taxonomy
) -> tuple[MatchResult, set[str] | None]:
    name = req.canonical_name
    known = taxonomy.get(name)

    ev = profile.skills.get(name) or (None if known else _term_evidence(profile, name))
    if ev:
        return _exact(req, ev), terms

    # Implied: a more specific skill evidences this one (Docker -> Containerization).
    implied_sources = [profile.skills[s] for s in taxonomy.implied_by.get(name, []) if s in profile.skills]
    if implied_sources:
        src = max(implied_sources, key=lambda e: EVIDENCE_RANK[e.evidence_level])
        return (
            MatchResult(
                requirement=req,
                match_type="implied",
                result_category="partial",
                similarity=0.85,
                confidence=0.7,
                credit=round(0.8 * EVIDENCE_CREDIT[src.evidence_level], 2),
                occurrences=src.occurrences,
                evidence_level=src.evidence_level,
                source_section=src.section_type,
                explanation=(
                    f"'{name}' is implied by '{src.canonical}' ({src.evidence_level}) {_where(src)}, "
                    f"but your resume does not name it directly. Consider naming it if accurate."
                ),
            ),
            terms,
        )

    # Fuzzy: typo/variant spelling not in the taxonomy (never across skill families).
    forms = [f for f in (taxonomy.all_forms(name) if known else [name]) if len(f) >= 5]
    if forms:
        if terms is None:
            terms = _resume_terms(profile)
        best_term, best_score = None, 0.0
        for form in forms:
            low = form.lower()
            for term in terms:
                if term[0] != low[0] or abs(len(term) - len(low)) > 2 or term == low:
                    continue
                if taxonomy.resolve(term):
                    continue  # a different known skill: never fuzzy-merge technologies
                score = _ratio(low, term)
                if score >= FUZZY_THRESHOLD and score > best_score:
                    best_term, best_score = term, score
        if best_term:
            return (
                MatchResult(
                    requirement=req,
                    match_type="fuzzy",
                    result_category="partial",
                    similarity=round(best_score / 100, 2),
                    confidence=round(best_score / 100 * 0.8, 2),
                    credit=round(min(0.8, best_score / 100 * 0.8), 2),
                    occurrences=1,
                    evidence_level=None,
                    source_section=None,
                    explanation=(
                        f"Resume contains '{best_term}', a close spelling of '{name}' "
                        f"({best_score:.0f}% similar). Check that it is the same technology."
                    ),
                ),
                terms,
            )

    # Semantic: same family only. Related, NOT verified.
    related = [profile.skills[r] for r in taxonomy.related(name) if r in profile.skills]
    related = [r for r in related if r.evidence_level != "mentioned"]
    if related:
        src = max(related, key=lambda e: EVIDENCE_RANK[e.evidence_level])
        credit = 0.3 if src.evidence_level == "demonstrated" else 0.2
        return (
            MatchResult(
                requirement=req,
                match_type="semantic",
                result_category="semantic",
                similarity=0.6,
                confidence=0.4,
                credit=min(credit, SEMANTIC_CAP),
                occurrences=src.occurrences,
                evidence_level=src.evidence_level,
                source_section=src.section_type,
                explanation=(
                    f"Related, not verified: your resume shows '{src.canonical}' ({src.evidence_level}) "
                    f"{_where(src)}, which is in the same family as '{name}'. Related experience "
                    f"does not count as proof of '{name}'."
                ),
            ),
            terms,
        )

    return _missing(req, f"'{name}' was not found in your resume."), terms


def _missing(req: ParsedRequirement, explanation: str) -> MatchResult:
    return MatchResult(
        requirement=req,
        match_type="missing",
        result_category=_categorize(req, "missing", None),
        similarity=0.0,
        confidence=0.9,
        credit=0.0,
        occurrences=0,
        evidence_level=None,
        source_section=None,
        explanation=explanation,
    )


def _match_experience(req: ParsedRequirement, profile: ResumeProfile) -> MatchResult:
    need = req.min_years or 0.0
    have = profile.years_experience
    if need <= 0:
        return _missing(req, "No year requirement could be read.")
    if have <= 0:
        return _missing(
            req,
            "Could not determine years of experience: no dated roles were found in the Experience "
            "section. Add start and end dates to each role.",
        )
    ratio = have / need
    if ratio >= 1:
        result = _missing(req, "")
        result.match_type, result.credit, result.similarity, result.confidence = "exact", 1.0, 1.0, 0.8
        result.result_category = "exact"
    elif ratio >= 0.5:
        result = _missing(req, "")
        result.match_type, result.credit = "partial", round(ratio, 2)
        result.similarity, result.confidence = round(ratio, 2), 0.7
        result.result_category = "partial"
    else:
        result = _missing(req, "")
        result.confidence = 0.7
    result.source_section = "experience"
    result.explanation = (
        f"Dated roles in your Experience section add up to about {have:g} years (overlaps merged); "
        f"the job asks for {need:g}+."
    )
    return result


def _match_education(req: ParsedRequirement, profile: ResumeProfile) -> MatchResult:
    need = _EDU_LEVEL.get(req.canonical_name, 2)
    have = profile.degree_level
    result = _missing(req, "")
    result.source_section = "education"
    if have >= need:
        result.match_type, result.credit, result.similarity, result.confidence = "exact", 1.0, 1.0, 0.8
        result.result_category = "exact"
        result.explanation = (
            f"Your education section shows a degree at or above the required level ({req.canonical_name})."
        )
    elif have > 0 and have == need - 1:
        result.match_type, result.credit, result.similarity, result.confidence = "partial", 0.5, 0.5, 0.6
        result.result_category = "partial"
        result.explanation = f"Your highest detected degree is one level below the {req.canonical_name} asked for."
    else:
        result.explanation = (
            "No degree was detected in your education section."
            if have == 0
            else f"Your highest detected degree is below the {req.canonical_name} asked for."
        )
    return result


def _match_responsibility(req: ParsedRequirement, profile: ResumeProfile, matcher: SemanticMatcher) -> MatchResult:
    pool = [u for u in profile.units if u.section_type in RESPONSIBILITY_SECTIONS]
    index, sim = matcher.best_match(req.canonical_name, [u.text for u in pool])
    if index < 0 or sim < 0.12:
        return _missing(req, "No resume sentence has meaningful wording overlap with this responsibility.")
    unit = pool[index]
    credit = round(min(1.0, max(0.0, (sim - 0.10) / 0.35)) * 0.8, 2)
    return MatchResult(
        requirement=req,
        match_type="semantic",
        result_category="semantic",
        similarity=sim,
        confidence=round(min(0.9, sim + 0.2), 2),
        credit=credit,
        occurrences=1,
        evidence_level=None,
        source_section=unit.section_type,
        explanation=(
            f'Wording overlap ({sim:.0%}) with: "{unit.text[:160]}". Overlap suggests related work; '
            f"it does not verify that you did this."
        ),
    )


def match_requirements(
    requirements: list[ParsedRequirement],
    profile: ResumeProfile,
    matcher: SemanticMatcher | None = None,
) -> list[MatchResult]:
    taxonomy = get_taxonomy()
    matcher = matcher or get_semantic_matcher()
    terms: set[str] | None = None
    results: list[MatchResult] = []
    for req in requirements:
        if req.kind in {"skill", "certification"}:
            result, terms = _match_skill(req, profile, terms, taxonomy)
        elif req.kind == "experience":
            result = _match_experience(req, profile)
        elif req.kind == "education":
            result = _match_education(req, profile)
        else:
            result = _match_responsibility(req, profile, matcher)
        if result.match_type == "missing":
            result.result_category = _categorize(req, "missing", None)
        elif result.match_type in {"exact", "partial"} and req.kind in {"experience", "education"}:
            pass  # category already set by the specific matcher
        results.append(result)
    return results
