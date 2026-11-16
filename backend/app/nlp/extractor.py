"""Builds a `ResumeProfile` (sections, skills with evidence, entities, stats) from resume sections.

This is the single entry point used on upload, reprocess and after a user corrects a
section, so the stored data always derives from the section text.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date

from app.document_processing.resume_entities import build_parsed_data
from app.document_processing.text_utils import merge_wrapped_lines, split_bullet, word_count
from app.nlp.skill_classifier import EVIDENCE_RANK, classify_evidence
from app.nlp.taxonomy import get_taxonomy

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z])")


@dataclass
class SectionInput:
    section_type: str
    heading_text: str | None
    content: str
    confidence: float = 0.8


@dataclass(frozen=True)
class Unit:
    text: str
    section_type: str
    is_bullet: bool


@dataclass
class SkillEvidence:
    canonical: str
    surface_form: str
    category: str
    evidence_level: str
    section_type: str | None
    snippet: str | None
    occurrences: int = 1


@dataclass
class ResumeProfile:
    raw_text: str
    sections: dict[str, str]
    section_types: list[str]
    heading_confidences: list[float]
    units: list[Unit]
    skills: dict[str, SkillEvidence]
    parsed: dict
    word_count: int
    bullet_count: int
    quantified_bullets: int
    extraction_confidence: float
    section_present: set[str] = field(default_factory=set)

    @property
    def years_experience(self) -> float:
        return float(self.parsed.get("estimated_years_experience", 0.0))

    @property
    def degree_level(self) -> int:
        return int(self.parsed.get("highest_degree_level", 0))


def _units_for(section: SectionInput) -> list[Unit]:
    units: list[Unit] = []
    for line in merge_wrapped_lines(section.content.splitlines()):
        text, is_bullet = split_bullet(line)
        if not text:
            continue
        parts = _SENTENCE_SPLIT.split(text) if len(text) > 220 else [text]
        units.extend(Unit(p.strip(), section.section_type, is_bullet) for p in parts if p.strip())
    return units


def build_profile(
    sections: list[SectionInput], extraction_confidence: float, today: date | None = None
) -> ResumeProfile:
    taxonomy = get_taxonomy()
    by_type: dict[str, list[str]] = {}
    raw_parts: list[str] = []
    units: list[Unit] = []
    for section in sections:
        by_type.setdefault(section.section_type, []).append(section.content)
        if section.heading_text:
            raw_parts.append(section.heading_text)
        raw_parts.append(section.content)
        units.extend(_units_for(section))
    joined = {k: "\n".join(v) for k, v in by_type.items()}
    raw_text = "\n".join(raw_parts)

    skills: dict[str, SkillEvidence] = {}
    for unit in units:
        if unit.section_type == "contact":
            continue
        for mention in taxonomy.find(unit.text):
            level = classify_evidence(unit.text, unit.section_type, unit.is_bullet)
            existing = skills.get(mention.canonical)
            snippet = unit.text if len(unit.text) <= 180 else unit.text[:177] + "..."
            if existing is None:
                skills[mention.canonical] = SkillEvidence(
                    canonical=mention.canonical,
                    surface_form=mention.surface,
                    category=taxonomy.category_of(mention.canonical),
                    evidence_level=level,
                    section_type=unit.section_type,
                    snippet=snippet,
                )
            else:
                existing.occurrences += 1
                if EVIDENCE_RANK[level] > EVIDENCE_RANK[existing.evidence_level]:
                    existing.evidence_level = level
                    existing.section_type = unit.section_type
                    existing.snippet = snippet
                    existing.surface_form = mention.surface

    parsed = build_parsed_data(joined, raw_text, today)
    work_units = [u for u in units if u.section_type in {"experience", "projects"} and u.is_bullet]
    quantified = sum(1 for u in work_units if re.search(r"\d|%", u.text))

    return ResumeProfile(
        raw_text=raw_text,
        sections=joined,
        section_types=[s.section_type for s in sections],
        heading_confidences=[s.confidence for s in sections if s.heading_text],
        units=units,
        skills=skills,
        parsed=parsed,
        word_count=word_count(raw_text),
        bullet_count=len(work_units),
        quantified_bullets=quantified,
        extraction_confidence=extraction_confidence,
        section_present={s.section_type for s in sections if s.content.strip()},
    )
