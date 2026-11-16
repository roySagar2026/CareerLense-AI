"""Runs the NLP pipeline for a stored resume + job and persists the explainable result."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.core.errors import AppError, not_found
from app.models import Analysis, JobRequirement, KeywordMatch, Recommendation, ResumeSection, User
from app.nlp.extractor import SectionInput, build_profile
from app.nlp.job_parser import ParsedRequirement
from app.nlp.pipeline import NoRequirementsError, run_analysis
from app.nlp.scorer import DISCLAIMER, FORMULA
from app.repositories import analyses as analyses_repo
from app.repositories import jobs as jobs_repo
from app.repositories import resumes as resumes_repo
from app.schemas.analysis import (
    AnalysisCreate,
    AnalysisDetailOut,
    AnalysisSummaryOut,
    CompareOut,
    DimensionOut,
    ScoringConfigOut,
    TrendPoint,
)
from app.services import audit


# ------------------------------------------------------------------ serialisers
def to_summary(analysis: Analysis) -> AnalysisSummaryOut:
    return AnalysisSummaryOut(
        id=analysis.id,
        resume_id=analysis.resume_id,
        resume_name=analysis.resume.name,
        resume_version=analysis.resume.version,
        job_id=analysis.job_id,
        job_title=analysis.job.title,
        company=analysis.job.company,
        overall_score=analysis.overall_score,
        status=analysis.status,
        engine_version=analysis.engine_version,
        dimension_scores={k: DimensionOut(**v) for k, v in analysis.dimension_scores.items()},
        created_at=analysis.created_at,
    )


def to_detail(analysis: Analysis) -> AnalysisDetailOut:
    summary = to_summary(analysis)
    return AnalysisDetailOut(
        **summary.model_dump(),
        disclaimer=DISCLAIMER,
        scoring_config=ScoringConfigOut(**analysis.scoring_config),
        metrics=analysis.metrics,
        keyword_counts=analysis.keyword_counts,
        skills_comparison=analysis.skills_comparison,
        section_analysis=analysis.section_analysis,
    )


# ------------------------------------------------------------------- operations
def create(db: Session, user: User, data: AnalysisCreate, ip: str | None = None) -> Analysis:
    resume = resumes_repo.get_owned(db, user.id, data.resume_id, detail=True)
    if resume is None:
        raise not_found("Resume")
    if resume.status != "ready":
        raise AppError(422, "validation_error", "This resume could not be processed. Fix or re-upload it first.")
    job = jobs_repo.get_owned(db, user.id, data.job_id, detail=True)
    if job is None:
        raise not_found("Job")

    ordered_sections = sorted(resume.sections, key=lambda s: s.order_index)
    profile = build_profile([_section_input(s) for s in ordered_sections], resume.extraction_confidence or 0.8)
    rows: list[JobRequirement] = list(job.requirements)
    requirements = [
        ParsedRequirement(
            kind=r.kind,
            canonical_name=r.canonical_name,
            surface_form=r.surface_form,
            importance=r.importance,
            category=r.category,
            evidence_snippet=r.evidence_snippet,
            min_years=r.min_years,
        )
        for r in rows
    ]
    try:
        output = run_analysis(profile, requirements, job.title, data.scoring_weights)
    except NoRequirementsError as exc:
        raise AppError(
            422,
            "no_requirements",
            "No skills or requirements could be extracted from this job description. Add more detail and try again.",
        ) from exc
    except ValueError as exc:
        raise AppError(422, "validation_error", str(exc)) from exc

    dims = {
        key: {
            "score": d.score,
            "weight": d.weight,
            "effective_weight": d.effective_weight,
            "contribution": d.contribution,
            "label": d.label,
            "explanation": d.explanation,
        }
        for key, d in output.score.dimensions.items()
    }
    analysis = Analysis(
        user_id=user.id,
        resume_id=resume.id,
        job_id=job.id,
        overall_score=output.score.overall,
        dimension_scores=dims,
        scoring_config={"weights": output.weights, "formula": FORMULA},
        metrics=output.score.metrics,
        keyword_counts=output.score.keyword_counts,
        section_analysis=output.section_analysis,
        skills_comparison=output.skills_comparison,
        status="completed",
        engine_version=output.engine_version,
    )
    db.add(analysis)
    db.flush()
    for index, match in enumerate(output.matches):
        req = match.requirement
        analysis.matches.append(
            KeywordMatch(
                requirement_id=rows[index].id,
                original_keyword=req.surface_form,
                normalized_keyword=req.canonical_name,
                kind=req.kind,
                importance=req.importance,
                category=req.category,
                match_type=match.match_type,
                result_category=match.result_category,
                similarity=match.similarity,
                confidence=match.confidence,
                credit=match.credit,
                occurrences=match.occurrences,
                evidence_level=match.evidence_level,
                source_section=match.source_section,
                suggested_section=match.suggested_section,
                explanation=match.explanation,
                order_index=index,
            )
        )
    for index, rec in enumerate(output.recommendations):
        analysis.recommendations.append(
            Recommendation(
                section_type=rec.section_type,
                priority=rec.priority,
                kind=rec.kind,
                title=rec.title,
                detail=rec.detail,
                related_keyword=rec.related_keyword,
                is_suggestion=True,
                caveat=rec.caveat,
                example_template=rec.example_template,
                order_index=index,
            )
        )
    audit.record(
        db,
        user.id,
        "analysis_create",
        resource_type="analysis",
        resource_id=analysis.id,
        label=f"Analyzed '{resume.name}' against '{job.title}' ({analysis.overall_score:.0f}/100)",
        ip=ip,
    )
    db.flush()
    analysis.resume, analysis.job = resume, job
    return analysis


def _section_input(section: ResumeSection) -> SectionInput:
    return SectionInput(section.section_type, section.heading_text, section.content, section.confidence)


def get(db: Session, user: User, analysis_id: uuid.UUID) -> Analysis:
    analysis = analyses_repo.get_owned(db, user.id, analysis_id)
    if analysis is None:
        raise not_found("Analysis")
    return analysis


def delete(db: Session, user: User, analysis_id: uuid.UUID) -> None:
    analysis = get(db, user, analysis_id)
    db.delete(analysis)
    audit.record(
        db, user.id, "analysis_delete", resource_type="analysis", resource_id=analysis_id, label="Deleted an analysis"
    )


def compare(db: Session, user: User, a_id: uuid.UUID, b_id: uuid.UUID) -> CompareOut:
    a, b = get(db, user, a_id), get(db, user, b_id)
    credit_a = {
        m.normalized_keyword: m for m in analyses_repo.all_matches(db, a.id) if m.kind in {"skill", "certification"}
    }
    credit_b = {
        m.normalized_keyword: m for m in analyses_repo.all_matches(db, b.id) if m.kind in {"skill", "certification"}
    }
    improved, regressed, unchanged_missing = [], [], []
    for keyword in sorted(set(credit_a) | set(credit_b)):
        ca = credit_a[keyword].credit if keyword in credit_a else None
        cb = credit_b[keyword].credit if keyword in credit_b else None
        if ca is None or cb is None:
            continue
        if cb > ca + 0.05:
            improved.append(keyword)
        elif cb < ca - 0.05:
            regressed.append(keyword)
        elif ca == 0 and cb == 0:
            unchanged_missing.append(keyword)
    deltas: dict[str, float | None] = {}
    for key in a.dimension_scores:
        sa, sb = a.dimension_scores[key]["score"], b.dimension_scores.get(key, {}).get("score")
        deltas[key] = round(sb - sa, 1) if sa is not None and sb is not None else None
    return CompareOut(
        a=to_summary(a),
        b=to_summary(b),
        score_delta=round(b.overall_score - a.overall_score, 1),
        dimension_deltas=deltas,
        improved_keywords=improved,
        regressed_keywords=regressed,
        unchanged_missing=unchanged_missing,
    )


def trend(db: Session, user: User, job_id: uuid.UUID) -> list[TrendPoint]:
    if jobs_repo.get_owned(db, user.id, job_id) is None:
        raise not_found("Job")
    rows = analyses_repo.for_job(db, user.id, job_id)
    rows.sort(key=lambda r: (r.resume.version, r.created_at))
    return [
        TrendPoint(
            analysis_id=r.id,
            resume_id=r.resume_id,
            resume_name=r.resume.name,
            resume_version=r.resume.version,
            overall_score=r.overall_score,
            created_at=r.created_at,
        )
        for r in rows
    ]
