"""Orchestrates one resume-vs-job analysis from parsed inputs. Pure Python, no DB access."""

from __future__ import annotations

from dataclasses import dataclass

from app.nlp.extractor import ResumeProfile
from app.nlp.job_parser import ParsedRequirement
from app.nlp.keyword_matcher import MatchResult, match_requirements
from app.nlp.recommendations import Recommendation, assign_placements, build_recommendations
from app.nlp.scorer import DISCLAIMER, FORMULA, ScoreResult, compute_score, resolve_weights
from app.nlp.section_analysis import analyze_sections

ENGINE_VERSION = "1.0.0"


class NoRequirementsError(Exception):
    """The job has nothing the engine can compare."""


@dataclass
class AnalysisOutput:
    score: ScoreResult
    weights: dict[str, float]
    matches: list[MatchResult]
    recommendations: list[Recommendation]
    section_analysis: list[dict]
    skills_comparison: list[dict]
    disclaimer: str = DISCLAIMER
    formula: str = FORMULA
    engine_version: str = ENGINE_VERSION


def _comparison(matches: list[MatchResult]) -> list[dict]:
    rows: list[dict] = []
    for m in matches:
        req = m.requirement
        if req.kind not in {"skill", "certification"} or req.importance == "contextual":
            continue
        if m.result_category == "exact":
            status = "matched"
        elif m.result_category in {"partial", "semantic"}:
            status = "partial"
        else:
            status = "missing"
        rows.append(
            {
                "keyword": req.canonical_name,
                "importance": req.importance,
                "status": status,
                "evidence_level": m.evidence_level,
                "match_type": m.match_type,
                "note": m.explanation,
            }
        )
    order = {"required": 0, "preferred": 1}
    rows.sort(key=lambda r: (order.get(r["importance"], 2), {"missing": 0, "partial": 1, "matched": 2}[r["status"]]))
    return rows


def run_analysis(
    profile: ResumeProfile,
    requirements: list[ParsedRequirement],
    job_title: str | None = None,
    weight_overrides: dict[str, float] | None = None,
) -> AnalysisOutput:
    if not requirements:
        raise NoRequirementsError("No requirements could be extracted from this job description.")
    weights = resolve_weights(weight_overrides)
    matches = match_requirements(requirements, profile)
    assign_placements(matches, profile)
    score = compute_score(matches, profile, weights)
    return AnalysisOutput(
        score=score,
        weights=weights,
        matches=matches,
        recommendations=build_recommendations(matches, profile, job_title),
        section_analysis=analyze_sections(profile, matches, job_title),
        skills_comparison=_comparison(matches),
    )
