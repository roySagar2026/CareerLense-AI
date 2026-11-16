"""Keyword placement and improvement recommendations.

Everything produced here is a *suggestion*. Placement text never states that the candidate
has a skill; every add-keyword suggestion carries a caveat and a template with [placeholders]
the candidate must fill with real facts.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.nlp.extractor import ResumeProfile
from app.nlp.keyword_matcher import MatchResult
from app.nlp.skill_classifier import EVIDENCE_RANK
from app.nlp.taxonomy import get_taxonomy

CAVEAT = "Only add this if you genuinely have this experience. CareerLens never verifies or invents experience."
WORK_CATEGORIES = {"language", "framework", "library", "database", "cloud", "devops", "tool", "data", "ai_ml", "os"}
PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


@dataclass
class Recommendation:
    section_type: str
    priority: str
    kind: str
    title: str
    detail: str
    related_keyword: str | None = None
    caveat: str | None = None
    example_template: str | None = None


def suggest_placement(match: MatchResult, profile: ResumeProfile) -> tuple[str, str]:
    """(section, reason) for a keyword the candidate could describe, if it is true for them."""
    taxonomy = get_taxonomy()
    req = match.requirement
    name = req.canonical_name
    present = profile.section_present
    if req.kind == "certification":
        return "certifications", "Credentials belong in a Certifications section."
    related = [profile.skills[r] for r in taxonomy.related(name) if r in profile.skills]
    related.sort(key=lambda e: EVIDENCE_RANK[e.evidence_level], reverse=True)
    for ev in related:
        if ev.section_type in {"experience", "projects"}:
            return (
                ev.section_type,
                f"Your {ev.section_type} section already shows related work with {ev.canonical}; "
                f"that is the natural place to state {name} if you also used it.",
            )
    category = req.category
    if category in WORK_CATEGORIES or category == "other":
        if "projects" in present:
            return (
                "projects",
                f"The job mentions {name}, and your resume has projects where its use could be described.",
            )
        if "experience" in present:
            return (
                "experience",
                f"The job mentions {name}; a role in your experience section is where its use would be shown.",
            )
        return "skills", f"Add {name} to a Skills section; there is no work section to attach it to yet."
    if category == "soft_skill":
        return "experience", f"Show {name.lower()} through a concrete accomplishment rather than a keyword."
    if "experience" in present:
        return "experience", f"{name} is best shown through what you did, in an experience bullet."
    return ("projects" if "projects" in present else "skills"), f"Describe {name} where you applied it."


def _template(match: MatchResult, section: str) -> str:
    name = match.requirement.canonical_name
    if match.requirement.kind == "certification":
        return f"{name} — [issuing body], [year earned or 'in progress']"
    if section == "skills":
        return f"[Category]: [skills you already list], {name}"
    return f"[Action verb] [what you built or did] using {name}, [how you applied it], [measurable result]"


def assign_placements(matches: list[MatchResult], profile: ResumeProfile) -> None:
    for match in matches:
        if match.requirement.kind in {"experience", "education", "responsibility"}:
            continue
        needs_placement = match.result_category in {
            "missing_mandatory",
            "missing_preferred",
            "semantic",
            "partial",
        } or (match.result_category == "contextual" and match.match_type == "missing")
        if not needs_placement:
            continue
        section, reason = suggest_placement(match, profile)
        match.suggested_section = section
        if match.match_type == "missing":
            match.explanation = f"{match.explanation} Suggested placement: {section.title()}. {reason}"


def build_recommendations(
    matches: list[MatchResult], profile: ResumeProfile, job_title: str | None = None
) -> list[Recommendation]:
    recs: list[Recommendation] = []
    missing_required = [
        m
        for m in matches
        if m.result_category == "missing_mandatory" and m.requirement.kind in {"skill", "certification"}
    ]
    missing_preferred = [
        m
        for m in matches
        if m.result_category == "missing_preferred" and m.requirement.kind in {"skill", "certification"}
    ]

    for match in missing_required[:12]:
        recs.append(_keyword_rec(match, "high", profile))
    for match in missing_preferred[:6]:
        recs.append(_keyword_rec(match, "medium", profile))

    for match in matches:
        req = match.requirement
        if req.kind != "skill":
            continue
        name = req.canonical_name
        if match.result_category == "semantic":
            recs.append(
                Recommendation(
                    section_type=match.suggested_section or "skills",
                    priority="medium" if req.importance == "required" else "low",
                    kind="verify",
                    title=f"Related experience found for {name}: state it only if it is true",
                    detail=match.explanation,
                    related_keyword=name,
                    caveat=CAVEAT,
                )
            )
        elif match.match_type == "exact" and match.evidence_level == "mentioned":
            recs.append(
                Recommendation(
                    section_type="experience" if "experience" in profile.section_present else "projects",
                    priority="medium",
                    kind="strengthen_evidence",
                    title=f"{name} appears only in passing",
                    detail=f"The job asks for {name} ({req.importance}) but your resume only mentions it incidentally. "
                    f"If you have used it, describe where and how in an experience or project bullet.",
                    related_keyword=name,
                    caveat=CAVEAT,
                    example_template=f"[Action verb] [what you built or did] using {name}, [measurable result]",
                )
            )
        elif match.match_type == "exact" and match.evidence_level == "listed" and req.importance == "required":
            recs.append(
                Recommendation(
                    section_type="experience" if "experience" in profile.section_present else "projects",
                    priority="medium",
                    kind="strengthen_evidence",
                    title=f"Show {name} in use, not only in the skills list",
                    detail=f"{name} is a required skill and is listed on your resume, but no experience or project bullet "
                    f"shows it in use, so it earns 70% credit instead of full credit.",
                    related_keyword=name,
                    caveat=CAVEAT,
                    example_template=f"[Action verb] [what you built or did] using {name}, [measurable result]",
                )
            )
        elif match.match_type == "fuzzy":
            recs.append(
                Recommendation(
                    section_type="skills",
                    priority="low",
                    kind="clarify",
                    title=f"Use the exact spelling '{name}'",
                    detail=match.explanation,
                    related_keyword=name,
                )
            )

    if profile.bullet_count and profile.quantified_bullets / profile.bullet_count < 0.3:
        recs.append(
            Recommendation(
                section_type="experience" if "experience" in profile.section_present else "projects",
                priority="medium",
                kind="quantify",
                title="Add measurable outcomes to more bullets",
                detail=f"Only {profile.quantified_bullets} of {profile.bullet_count} accomplishment bullets contain a number or percentage. "
                f"Where it is true, state scale, speed, accuracy or usage (users, requests, time saved).",
                example_template="[Action verb] [what], resulting in [number or %] [improvement] over [period or baseline]",
            )
        )
    if "skills" not in profile.section_present:
        recs.append(
            Recommendation(
                section_type="skills",
                priority="high",
                kind="structure",
                title="Add a clearly labelled Skills section",
                detail="Recruiters and parsers look for a Skills section. Group what you genuinely know by category "
                "(Languages, Frameworks, Databases, Tools).",
                example_template="Languages: [..]  |  Frameworks: [..]  |  Tools: [..]",
            )
        )
    if "summary" not in profile.section_present and job_title:
        recs.append(
            Recommendation(
                section_type="summary",
                priority="low",
                kind="clarify",
                title="Consider a short summary aligned with the role",
                detail=f"A 2-3 line summary can state your target direction (for example: {job_title}). Keep every claim factual.",
                example_template="[Role] with [N years or 'recent graduate'] experience in [areas]; focused on [goal].",
            )
        )
    if profile.extraction_confidence < 0.6:
        recs.append(
            Recommendation(
                section_type="other",
                priority="high",
                kind="structure",
                title="Resume text was hard to extract",
                detail="Low extraction confidence usually means a scanned PDF, text in images or an unusual layout. "
                "Export a text-based PDF or DOCX and re-upload so the analysis reads everything.",
            )
        )
    recs.sort(key=lambda r: PRIORITY_ORDER[r.priority])
    return recs


def _keyword_rec(match: MatchResult, priority: str, profile: ResumeProfile) -> Recommendation:
    req = match.requirement
    section = match.suggested_section or suggest_placement(match, profile)[0]
    _, reason = suggest_placement(match, profile)
    job_context = f' The job says: "{req.evidence_snippet}"' if req.evidence_snippet else ""
    return Recommendation(
        section_type=section,
        priority=priority,
        kind="add_keyword",
        title=f"If you have used {req.canonical_name}, show it in {section.title()}",
        detail=f"{req.canonical_name} is {req.importance} for this role and is missing from your resume.{job_context} {reason}",
        related_keyword=req.canonical_name,
        caveat=CAVEAT,
        example_template=_template(match, section),
    )
