from __future__ import annotations

from datetime import date

import pytest

from app.document_processing.docx_parser import parse_docx
from app.document_processing.models import Line
from app.document_processing.section_detector import classify_heading, detect_sections
from app.nlp.extractor import SectionInput, build_profile
from app.nlp.job_parser import parse_job, years_required
from app.nlp.keyword_matcher import match_requirements
from app.nlp.pipeline import NoRequirementsError, run_analysis
from app.nlp.scorer import DEFAULT_WEIGHTS, resolve_weights
from app.nlp.semantic_matcher import TfidfSemanticMatcher
from app.nlp.taxonomy import get_taxonomy
from tests.synthetic import JOB_TEXT, RESUME_BLOCKS, make_docx

TODAY = date(2025, 1, 1)


def profile_from_blocks(blocks=RESUME_BLOCKS):
    parsed = parse_docx(make_docx(blocks))
    sections = detect_sections(parsed.lines)
    inputs = [SectionInput(s.section_type, s.heading_text, s.content, s.confidence) for s in sections]
    return build_profile(inputs, parsed.extraction_confidence, today=TODAY)


def profile_from_text(**sections: str):
    inputs = [SectionInput(k, k.title(), v, 0.9) for k, v in sections.items()]
    return build_profile(inputs, 0.9, today=TODAY)


@pytest.fixture(scope="module")
def profile():
    return profile_from_blocks()


# ------------------------------------------------------------------ parsing
def test_docx_sections_detected(profile):
    assert {"contact", "summary", "skills", "experience", "projects", "education", "certifications"} <= set(
        profile.section_types
    )


def test_heading_classification_rules():
    assert classify_heading(Line("EXPERIENCE", bold=True))[0] == "experience"
    assert classify_heading(Line("Technical Skills & Tools", bold=True))[0] == "skills"
    assert classify_heading(Line("Experience with Python is required.")) is None
    assert classify_heading(Line("Built APIs for 20 clients")) is None


def test_docx_table_and_text_order():
    import io

    from docx import Document

    doc = Document()
    doc.add_paragraph("SKILLS")
    table = doc.add_table(rows=1, cols=2)
    table.rows[0].cells[0].text = "Languages"
    table.rows[0].cells[1].text = "Python, Go"
    buffer = io.BytesIO()
    doc.save(buffer)
    parsed = parse_docx(buffer.getvalue())
    assert "Languages | Python, Go" in [ln.text for ln in parsed.lines]


def test_corrupt_docx_raises():
    from app.document_processing.models import DocumentParseError

    with pytest.raises(DocumentParseError):
        parse_docx(b"not a docx")


def test_entities(profile):
    contact = profile.parsed["contact"]
    assert contact["name"] == "Asha Verma"
    assert contact["email"] == "asha.verma@example.com"
    assert contact["phone"] and "98765" in contact["phone"]
    experience = profile.parsed["experience"]
    assert [e["organization"] for e in experience] == ["Northwind Labs", "Acme Systems"]
    assert experience[0]["title"] == "Software Engineer"
    assert experience[0]["date_range"].startswith("Jan 2022")
    assert len(experience[0]["bullets"]) == 3
    assert 4.5 <= profile.years_experience <= 5.0  # Jun 2020 - Dec 2021 + Jan 2022 - Jan 2025
    assert profile.degree_level == 2
    assert profile.parsed["projects"][0]["tech"][:2] == ["Python", "Flask"]


# ----------------------------------------------------------------- taxonomy
def test_taxonomy_normalisation_and_boundaries():
    tax = get_taxonomy()
    names = lambda text: [m.canonical for m in tax.find(text)]  # noqa: E731
    assert names("Knows JS and py") == ["JavaScript", "Python"]
    assert names("Postgres, CI/CD, RESTful API") == ["PostgreSQL", "CI/CD", "REST API"]
    assert names("JavaScript developer") == ["JavaScript"]  # not Java
    assert names("Built things with C++ and C#") == ["C++", "C#"]
    assert names("Languages: Python, C, R") == ["Python", "C", "R"]
    assert names("Grade C in school; Vitamin C") == []
    assert names("We use Go and Rust") == ["Go", "Rust"]
    assert names("Go to market strategy") == []
    assert names("react to incidents quickly") == []  # case-sensitive React
    assert names("Built UIs in React.js") == ["React"]
    assert names("see https://github.com/someone/python-flask-app") == []  # URLs ignored
    assert names("NoSQL and SQL") == ["NoSQL", "SQL"]


def test_flask_is_not_django():
    tax = get_taxonomy()
    assert tax.resolve("Flask") != tax.resolve("Django")
    assert tax.same_family("Flask", "Django")
    assert "Django" in tax.related("Flask")


# ------------------------------------------------------------------ evidence
def test_evidence_levels(profile):
    skills = profile.skills
    assert skills["Python"].evidence_level == "demonstrated"
    assert skills["Redis"].evidence_level == "demonstrated"  # Tech: line in a project
    assert skills["C++"].evidence_level == "listed"  # only in the skills list
    assert skills["Linux"].evidence_level == "listed"


def test_aspirational_mention_is_not_demonstrated():
    p = profile_from_text(
        experience="Software Engineer, Acme   Jan 2022 - Present\n• Currently learning Kubernetes in my spare time",
        skills="Languages: Python",
    )
    assert p.skills["Kubernetes"].evidence_level == "mentioned"


def test_repeated_keyword_does_not_inflate_score():
    base = "Software Engineer, Acme   Jan 2022 - Present\n• Built services using Python"
    repeated = base + "\n" + "\n".join("• Built more services using Python" for _ in range(10))
    job = parse_job("Requirements\n- Python\n- Docker")
    scores = []
    for exp in (base, repeated):
        prof = profile_from_text(experience=exp, skills="Python")
        scores.append(run_analysis(prof, job.requirements).score.dimensions["required_skills"].score)
    assert scores[0] == scores[1]


# ---------------------------------------------------------------------- job
def test_job_parsing():
    job = parse_job(JOB_TEXT)
    assert job.title_guess == "Backend Engineer"
    by_name = {(r.kind, r.canonical_name): r for r in job.requirements}
    assert by_name[("skill", "Python")].importance == "required"
    assert by_name[("skill", "Terraform")].importance == "preferred"
    assert by_name[("certification", "AWS Certified Solutions Architect")].importance == "preferred"
    assert by_name[("skill", "Docker")].importance == "required"  # in Responsibilities
    assert by_name[("education", "Bachelor's degree")].importance == "required"
    assert years_required(job.requirements) == 3.0
    assert any(r.kind == "responsibility" for r in job.requirements)
    assert ("skill", "Kubernetes") in by_name


def test_job_unlisted_terms_and_degree_false_positive():
    job = parse_job("Requirements\n- Experience with FHIR and HL7\n- Proficiency in MS Office")
    names = {r.canonical_name for r in job.requirements}
    assert {"FHIR", "HL7"} <= names
    assert not any(r.kind == "education" for r in job.requirements)  # 'MS Office' is not a Master's


# ------------------------------------------------------------------ matching
def test_match_tiers(profile):
    job = parse_job(JOB_TEXT)
    matches = {m.requirement.canonical_name: m for m in match_requirements(job.requirements, profile)}
    assert matches["Python"].match_type == "exact" and matches["Python"].credit == 1.0
    assert matches["Django"].match_type == "semantic"  # Flask is related, not verified
    assert matches["Django"].credit <= 0.4
    assert matches["Django"].result_category == "semantic"
    assert matches["Docker"].match_type == "missing"
    assert matches["Docker"].result_category == "missing_mandatory"
    assert matches["Terraform"].result_category == "missing_preferred"
    assert matches["Bachelor's degree"].match_type == "exact"
    exp = next(m for m in matches.values() if m.requirement.kind == "experience")
    assert exp.match_type == "exact"


def test_fuzzy_match_variant_spelling_but_not_across_technologies():
    p = profile_from_text(skills="Tools: Kubernets, Jenkins")
    job = parse_job("Requirements\n- Kubernetes\n- GitLab CI")
    matches = {m.requirement.canonical_name: m for m in match_requirements(job.requirements, p)}
    assert matches["Kubernetes"].match_type == "fuzzy"
    # Jenkins is the same family as GitLab CI -> related only, never merged
    assert matches["GitLab CI"].match_type == "semantic"


def test_implied_skill():
    p = profile_from_text(
        experience="Engineer, Acme   Jan 2023 - Present\n• Built and deployed services using Docker",
    )
    job = parse_job("Requirements\n- Containerization")
    match = match_requirements(job.requirements, p)[0]
    assert match.match_type == "implied" and match.result_category == "partial"
    assert 0.7 <= match.credit <= 0.8


def test_semantic_matcher_prefers_related_text():
    matcher = TfidfSemanticMatcher()
    idx, sim = matcher.best_match(
        "Design and build REST APIs in Python",
        ["Cooked dinner for friends", "Built REST APIs in Python and Flask", "Organised the annual picnic"],
    )
    assert idx == 1 and sim > 0.3
    assert matcher.best_match("anything", []) == (-1, 0.0)


# ------------------------------------------------------------------- scoring
def test_end_to_end_analysis(profile):
    job = parse_job(JOB_TEXT)
    out = run_analysis(profile, job.requirements, job.title_guess)
    assert 0 <= out.score.overall <= 100
    total_contribution = sum(d.contribution for d in out.score.dimensions.values())
    assert abs(total_contribution - out.score.overall) <= 0.3
    assert sum(d.effective_weight or 0 for d in out.score.dimensions.values()) == pytest.approx(100, abs=0.5)
    assert "NOT the score" in out.disclaimer
    assert out.score.keyword_counts["missing_mandatory"] >= 1
    docker = next(m for m in out.matches if m.requirement.canonical_name == "Docker")
    assert docker.suggested_section in {"projects", "experience"}
    assert "Suggested placement" in docker.explanation
    rec = next(r for r in out.recommendations if r.related_keyword == "Docker")
    assert rec.kind == "add_keyword" and rec.caveat and "[" in (rec.example_template or "")
    assert out.section_analysis and {s["section_type"] for s in out.section_analysis} >= {"skills", "experience"}


def test_weight_redistribution_when_dimension_not_applicable():
    p = profile_from_text(
        skills="Python", experience="Engineer, Acme   Jan 2022 - Present\n• Built services using Python"
    )
    job = parse_job("Requirements\n- Python")  # no preferred / responsibilities / education / years
    out = run_analysis(p, job.requirements)
    dims = out.score.dimensions
    assert dims["preferred_skills"].score is None and dims["preferred_skills"].effective_weight is None
    assert dims["required_skills"].effective_weight is not None


def test_custom_weights_validation():
    assert resolve_weights(None) == DEFAULT_WEIGHTS
    with pytest.raises(ValueError):
        resolve_weights({"required_skills": -1})
    with pytest.raises(ValueError):
        resolve_weights({"nonsense": 5})
    with pytest.raises(ValueError):
        resolve_weights({k: 0 for k in DEFAULT_WEIGHTS})


def test_empty_job_raises():
    with pytest.raises(NoRequirementsError):
        run_analysis(profile_from_text(skills="Python"), [])
