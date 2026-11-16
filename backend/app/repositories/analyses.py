from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models import Analysis, JobDescription, KeywordMatch, Recommendation, Resume


def get_owned(db: Session, user_id: uuid.UUID, analysis_id: uuid.UUID) -> Analysis | None:
    stmt = (
        select(Analysis)
        .options(joinedload(Analysis.resume), joinedload(Analysis.job))
        .where(Analysis.id == analysis_id, Analysis.user_id == user_id)
    )
    return db.scalars(stmt).first()


def list_page(
    db: Session,
    user_id: uuid.UUID,
    *,
    company: str | None,
    job_title: str | None,
    resume_id: uuid.UUID | None,
    job_id: uuid.UUID | None,
    offset: int,
    limit: int,
) -> tuple[list[Analysis], int]:
    base = (
        select(Analysis)
        .join(Resume, Analysis.resume_id == Resume.id)
        .join(JobDescription, Analysis.job_id == JobDescription.id)
        .where(Analysis.user_id == user_id)
    )
    if company:
        base = base.where(JobDescription.company.ilike(f"%{company}%"))
    if job_title:
        base = base.where(JobDescription.title.ilike(f"%{job_title}%"))
    if resume_id:
        base = base.where(Analysis.resume_id == resume_id)
    if job_id:
        base = base.where(Analysis.job_id == job_id)
    total = db.scalar(select(func.count()).select_from(base.subquery())) or 0
    stmt = (
        base.options(joinedload(Analysis.resume), joinedload(Analysis.job))
        .order_by(Analysis.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    return list(db.scalars(stmt).unique()), int(total)


def keyword_page(
    db: Session,
    analysis_id: uuid.UUID,
    *,
    filters: dict[str, str | None],
    search: str | None,
    offset: int,
    limit: int,
) -> tuple[list[KeywordMatch], int]:
    base = select(KeywordMatch).where(KeywordMatch.analysis_id == analysis_id)
    for column, value in filters.items():
        if value:
            base = base.where(getattr(KeywordMatch, column) == value)
    if search:
        base = base.where(KeywordMatch.original_keyword.ilike(f"%{search}%"))
    total = db.scalar(select(func.count()).select_from(base.subquery())) or 0
    rows = db.scalars(base.order_by(KeywordMatch.order_index).offset(offset).limit(limit))
    return list(rows), int(total)


def all_matches(db: Session, analysis_id: uuid.UUID) -> list[KeywordMatch]:
    return list(db.scalars(select(KeywordMatch).where(KeywordMatch.analysis_id == analysis_id)))


def recommendations(
    db: Session, analysis_id: uuid.UUID, priority: str | None, section: str | None
) -> list[Recommendation]:
    stmt = select(Recommendation).where(Recommendation.analysis_id == analysis_id)
    if priority:
        stmt = stmt.where(Recommendation.priority == priority)
    if section:
        stmt = stmt.where(Recommendation.section_type == section)
    return list(db.scalars(stmt.order_by(Recommendation.order_index)))


def for_job(db: Session, user_id: uuid.UUID, job_id: uuid.UUID) -> list[Analysis]:
    stmt = (
        select(Analysis)
        .options(joinedload(Analysis.resume))
        .where(Analysis.user_id == user_id, Analysis.job_id == job_id)
        .order_by(Analysis.created_at)
    )
    return list(db.scalars(stmt).unique())
