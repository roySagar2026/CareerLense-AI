"""Explainable weighted alignment scoring.

overall = sum(effective_weight_i/100 * score_i) over the dimensions that apply to the job.
A dimension with no matching job requirements (score None) is skipped and its weight is
redistributed proportionally. Each requirement counts ONCE, whatever the number of
occurrences, and its credit depends on the evidence level. This is a heuristic alignment
score, not an employer ATS score.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.nlp.extractor import ResumeProfile
from app.nlp.keyword_matcher import MatchResult

DEFAULT_WEIGHTS: dict[str, float] = {
    "required_skills": 35.0,
    "preferred_skills": 15.0,
    "experience": 20.0,
    "responsibilities": 15.0,
    "education": 10.0,
    "structure": 5.0,
}
LABELS = {
    "required_skills": "Required skills",
    "preferred_skills": "Preferred skills",
    "experience": "Experience",
    "responsibilities": "Responsibilities",
    "education": "Education & certifications",
    "structure": "Resume structure",
}
IMPORTANCE_WEIGHT = {"required": 1.0, "preferred": 1.0, "contextual": 0.3}
DISCLAIMER = (
    "This is a heuristic alignment score computed by CareerLens AI from keyword and context "
    "analysis. It is NOT the score of any employer's applicant tracking system (ATS), and it "
    "does not predict hiring outcomes."
)
FORMULA = (
    "overall = Σ(effective_weight × dimension_score) / 100, where effective_weight = weight ÷ "
    "(sum of weights of the dimensions that apply to this job) × 100. Each requirement counts once; "
    "credit = 1.0 demonstrated, 0.7 listed, 0.35 passing mention, ≤0.8 typo/variant match, "
    "0.3 related-skill (not verified), 0 missing."
)
RESULT_CATEGORIES = ("exact", "semantic", "partial", "missing_mandatory", "missing_preferred", "contextual")


@dataclass
class Dimension:
    score: float | None
    weight: float
    effective_weight: float | None
    contribution: float
    label: str
    explanation: str


@dataclass
class ScoreResult:
    overall: float
    dimensions: dict[str, Dimension]
    metrics: dict[str, float | None]
    keyword_counts: dict[str, int]
    structure_checks: list[dict] = field(default_factory=list)


def resolve_weights(overrides: dict[str, float] | None) -> dict[str, float]:
    weights = dict(DEFAULT_WEIGHTS)
    for key, value in (overrides or {}).items():
        if key not in weights:
            raise ValueError(f"Unknown scoring dimension: {key}")
        if not 0 <= float(value) <= 100:
            raise ValueError("Scoring weights must be between 0 and 100.")
        weights[key] = float(value)
    if sum(weights.values()) <= 0:
        raise ValueError("At least one scoring weight must be greater than 0.")
    return weights


def structure_score(profile: ResumeProfile) -> tuple[float, list[dict]]:
    contact = profile.parsed.get("contact", {})
    present = profile.section_present
    heading_ok = (
        sum(1 for c in profile.heading_confidences if c >= 0.8) / len(profile.heading_confidences)
        if profile.heading_confidences
        else 0.0
    )
    quantified_ratio = profile.quantified_bullets / profile.bullet_count if profile.bullet_count else 0.0
    checks = [
        ("Email address found", 10, bool(contact.get("email")), "Add a professional email address."),
        ("Phone number found", 5, bool(contact.get("phone")), "Add a phone number."),
        ("Skills section present", 15, "skills" in present, "Add a clearly labelled Skills section."),
        (
            "Experience or Projects present",
            20,
            bool(present & {"experience", "projects"}),
            "Add Experience or Projects with described work.",
        ),
        ("Education section present", 10, "education" in present, "Add an Education section."),
        ("Summary present", 5, "summary" in present, "Add a short professional summary."),
        (
            "Standard section headings",
            5,
            heading_ok >= 0.6,
            "Use standard headings such as Skills, Experience, Education.",
        ),
        (
            "Described accomplishments (6+ bullets)",
            10,
            profile.bullet_count >= 6,
            "Use bullet points to describe what you did.",
        ),
        (
            "Measurable results in 25%+ of bullets",
            10,
            quantified_ratio >= 0.25,
            "Add numbers (%, counts, time saved) where truthful.",
        ),
        (
            "Reasonable length (250-1100 words)",
            10,
            250 <= profile.word_count <= 1100,
            "Aim for roughly one to two pages.",
        ),
    ]
    rows = [
        {"name": n, "points": p, "earned": p if ok else 0, "passed": ok, "hint": None if ok else h}
        for n, p, ok, h in checks
    ]
    return float(sum(r["earned"] for r in rows)), rows


def _weighted_mean(matches: list[MatchResult]) -> float | None:
    if not matches:
        return None
    total = sum(IMPORTANCE_WEIGHT[m.requirement.importance] for m in matches)
    value = sum(IMPORTANCE_WEIGHT[m.requirement.importance] * m.credit for m in matches)
    return round(100 * value / total, 1) if total else None


def _found(matches: list[MatchResult]) -> str:
    return f"{sum(1 for m in matches if m.credit > 0)} of {len(matches)} requirements matched"


def compute_score(matches: list[MatchResult], profile: ResumeProfile, weights: dict[str, float]) -> ScoreResult:
    skills = [m for m in matches if m.requirement.kind == "skill"]
    required = [m for m in skills if m.requirement.importance == "required"]
    preferred = [m for m in skills if m.requirement.importance != "required"]
    experience = [m for m in matches if m.requirement.kind == "experience"]
    responsibilities = [m for m in matches if m.requirement.kind == "responsibility"]
    education = [m for m in matches if m.requirement.kind in {"education", "certification"}]

    exp_years = _weighted_mean(experience)
    demonstrated = (
        100 * sum(1 for m in required if m.evidence_level == "demonstrated" and m.match_type == "exact") / len(required)
        if required
        else None
    )
    if exp_years is not None and demonstrated is not None:
        exp_score: float | None = round(0.6 * exp_years + 0.4 * demonstrated, 1)
        exp_note = f"60% years of experience ({exp_years:.0f}), 40% required skills shown in work ({demonstrated:.0f})."
    elif exp_years is not None:
        exp_score, exp_note = exp_years, "Years of experience versus the job's requirement."
    elif demonstrated is not None:
        exp_score = round(demonstrated, 1)
        exp_note = "Share of required skills that are demonstrated in Experience/Projects (the job states no years)."
    else:
        exp_score, exp_note = None, "The job has no experience requirement to compare."

    struct, checks = structure_score(profile)
    scores: dict[str, tuple[float | None, str]] = {
        "required_skills": (_weighted_mean(required), f"{_found(required)}; credit reflects evidence strength.")
        if required
        else (None, "The job lists no required skills."),
        "preferred_skills": (_weighted_mean(preferred), f"{_found(preferred)} (contextual keywords weigh 0.3).")
        if preferred
        else (None, "The job lists no preferred skills."),
        "experience": (exp_score, exp_note),
        "responsibilities": (
            _weighted_mean(responsibilities),
            f"{_found(responsibilities)} by wording overlap (not verified).",
        )
        if responsibilities
        else (None, "No responsibilities were detected in the job text."),
        "education": (_weighted_mean(education), f"{_found(education)}.")
        if education
        else (None, "The job states no education or certification requirement."),
        "structure": (struct, f"{sum(1 for c in checks if c['passed'])} of {len(checks)} structure checks passed."),
    }

    active_total = sum(weights[k] for k, (s, _) in scores.items() if s is not None)
    if active_total <= 0:
        raise ValueError("No scoring dimension with a positive weight applies to this job.")

    dimensions: dict[str, Dimension] = {}
    overall = 0.0
    for key, (score, note) in scores.items():
        if score is None or weights[key] <= 0:
            dimensions[key] = Dimension(score, weights[key], None if score is None else 0.0, 0.0, LABELS[key], note)
            continue
        effective = weights[key] / active_total * 100
        contribution = effective / 100 * score
        overall += contribution
        dimensions[key] = Dimension(score, weights[key], round(effective, 1), round(contribution, 1), LABELS[key], note)

    keyword_skills = [m for m in matches if m.requirement.kind in {"skill", "certification"}]
    counts = {c: 0 for c in RESULT_CATEGORIES}
    for m in matches:
        counts[m.result_category] = counts.get(m.result_category, 0) + 1
    metrics = {
        "skills_alignment": _weighted_mean(
            required + [m for m in preferred if m.requirement.importance == "preferred"]
        ),
        "keyword_coverage": round(100 * sum(1 for m in keyword_skills if m.credit > 0) / len(keyword_skills), 1)
        if keyword_skills
        else None,
        "structural_quality": struct,
        "experience_alignment": exp_score,
        "education_alignment": _weighted_mean(education),
    }
    return ScoreResult(round(overall, 1), dimensions, metrics, counts, checks)
