"""Per-section analysis: strengths, gaps, relevant keywords, recommendations, priority."""

from __future__ import annotations

from app.nlp.extractor import ResumeProfile
from app.nlp.keyword_matcher import MatchResult

SECTIONS = ("summary", "skills", "experience", "projects", "education", "certifications")
_PRIORITY_RANK = {"low": 0, "medium": 1, "high": 2}


def _raise(current: str, wanted: str) -> str:
    return wanted if _PRIORITY_RANK[wanted] > _PRIORITY_RANK[current] else current


def analyze_sections(profile: ResumeProfile, matches: list[MatchResult], job_title: str | None = None) -> list[dict]:
    present = profile.section_present
    keyword_matches = [m for m in matches if m.requirement.kind in {"skill", "certification"}]
    found_by_section: dict[str, list[str]] = {}
    for m in keyword_matches:
        if m.match_type == "exact" and m.source_section:
            found_by_section.setdefault(m.source_section, []).append(m.requirement.canonical_name)
    missing_by_section: dict[str, list[MatchResult]] = {}
    for m in keyword_matches:
        if m.result_category in {"missing_mandatory", "missing_preferred"} and m.suggested_section:
            missing_by_section.setdefault(m.suggested_section, []).append(m)

    has_cert_req = any(m.requirement.kind == "certification" for m in matches)
    has_edu_req = any(m.requirement.kind == "education" for m in matches)
    results: list[dict] = []

    for section in SECTIONS:
        strengths: list[str] = []
        missing: list[str] = []
        recs: list[str] = []
        priority = "low"
        is_present = section in present
        text = profile.sections.get(section, "")

        if not is_present:
            if section == "skills":
                missing.append("No dedicated Skills section found.")
                recs.append("Add a Skills section grouped by category (languages, frameworks, tools).")
                priority = "high"
            elif section == "experience":
                if "projects" in present:
                    missing.append("No Experience section; your Projects carry the evidence.")
                    priority = "medium"
                else:
                    missing.append("No Experience or Projects section found.")
                    recs.append("Add work, internship or project experience with described accomplishments.")
                    priority = "high"
            elif section == "projects":
                if "experience" not in present:
                    missing.append("No Projects section found.")
                    recs.append("Add projects that show the skills the job asks for.")
                    priority = "high"
                else:
                    missing.append("No Projects section (optional when you have work experience).")
            elif section == "education":
                missing.append("No Education section found.")
                priority = "high" if has_edu_req else "medium"
                recs.append("Add your degree, institution and year.")
            elif section == "certifications":
                if has_cert_req:
                    missing.append("The job mentions certifications but your resume has no Certifications section.")
                    priority = "medium"
                    recs.append("List relevant certifications you actually hold (name, issuer, year).")
            elif section == "summary":
                missing.append("No professional summary.")
                priority = "low"
                recs.append(f"Optionally add a 2-3 line summary aligned with {job_title or 'the target role'}.")
        else:
            if section == "summary":
                words = len(text.split())
                if words > 90:
                    missing.append(f"Summary is long ({words} words).")
                    recs.append("Trim the summary to 2-3 lines.")
                    priority = "low"
                else:
                    strengths.append("Concise summary present.")
                if job_title and any(w in text.lower() for w in job_title.lower().split() if len(w) > 3):
                    strengths.append("Summary echoes the target role.")
            elif section == "skills":
                listed = [s for s in profile.skills.values() if s.section_type == "skills"]
                strengths.append(f"{len(listed)} recognised skills listed.")
                shown_elsewhere = [
                    m.requirement.canonical_name
                    for m in keyword_matches
                    if m.match_type == "exact"
                    and m.source_section in {"experience", "projects"}
                    and m.requirement.canonical_name not in {s.canonical for s in listed}
                ]
                if shown_elsewhere:
                    missing.append(
                        "Skills used in your work but not in your Skills list: " + ", ".join(shown_elsewhere[:6]) + "."
                    )
                    recs.append("List skills you demonstrate in Experience/Projects in your Skills section too.")
                    priority = _raise(priority, "medium")
                if "\n" not in text.strip() and len(text) > 300:
                    recs.append("Break the skills into labelled groups instead of one long line.")
            elif section in {"experience", "projects"}:
                entries = profile.parsed.get("experience" if section == "experience" else "projects", [])
                bullets = sum(len(e.get("bullets", [])) for e in entries)
                if entries:
                    strengths.append(f"{len(entries)} {'roles' if section == 'experience' else 'projects'} detected.")
                if bullets < 3:
                    missing.append("Few described accomplishments.")
                    recs.append("Describe what you built or achieved in 2-4 bullets per entry.")
                    priority = _raise(priority, "medium")
                elif profile.bullet_count and profile.quantified_bullets / max(profile.bullet_count, 1) < 0.3:
                    missing.append("Few bullets include measurable outcomes.")
                    recs.append("Add numbers (%, counts, time saved) where truthful.")
                    priority = _raise(priority, "medium")
                else:
                    strengths.append("Bullets include measurable results.")
                if section == "projects":
                    untech = [e["name"] for e in entries if not e.get("tech")]
                    if untech:
                        missing.append(f"No tech stack stated for: {', '.join(untech[:3])}.")
                        recs.append("Add a 'Tech:' line to each project so tools are explicit.")
                if section == "experience" and profile.years_experience:
                    strengths.append(f"About {profile.years_experience:g} years of dated experience.")
            elif section == "education":
                if profile.degree_level:
                    strengths.append("Degree detected.")
                else:
                    missing.append("No degree recognised in the Education section.")
                    recs.append("State the degree name explicitly (for example B.Tech in Computer Science).")
                    priority = "high" if has_edu_req else "medium"
            elif section == "certifications":
                strengths.append(f"{len(profile.parsed.get('certifications', []))} certification entries.")

        pending = missing_by_section.get(section, [])
        if pending:
            names = [m.requirement.canonical_name for m in pending[:6]]
            missing.append("Job keywords you could add here if true: " + ", ".join(names) + ".")
            if any(m.result_category == "missing_mandatory" for m in pending):
                priority = _raise(priority, "high")
            else:
                priority = _raise(priority, "medium")

        results.append(
            {
                "section_type": section,
                "present": is_present,
                "priority": priority,
                "strengths": strengths,
                "missing": missing,
                "relevant_keywords": sorted(set(found_by_section.get(section, [])))[:15],
                "recommendations": recs,
            }
        )
    return results
