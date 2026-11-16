from __future__ import annotations

import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models import JobDescription, JobRequirement


def get_owned(db: Session, user_id: uuid.UUID, job_id: uuid.UUID, *, detail: bool = False) -> JobDescription | None:
    stmt = select(JobDescription).where(JobDescription.id == job_id, JobDescription.user_id == user_id)
    if detail:
        stmt = stmt.options(selectinload(JobDescription.requirements))
    return db.scalars(stmt).first()


def list_page(
    db: Session, user_id: uuid.UUID, search: str | None, offset: int, limit: int
) -> tuple[list[JobDescription], int]:
    base = select(JobDescription).where(JobDescription.user_id == user_id)
    if search:
        like = f"%{search}%"
        base = base.where(or_(JobDescription.title.ilike(like), JobDescription.company.ilike(like)))
    total = db.scalar(select(func.count()).select_from(base.subquery())) or 0
    rows = db.scalars(base.order_by(JobDescription.created_at.desc()).offset(offset).limit(limit))
    return list(rows), int(total)


def requirement_counts(db: Session, job_ids: list[uuid.UUID]) -> dict[uuid.UUID, int]:
    if not job_ids:
        return {}
    stmt = (
        select(JobRequirement.job_id, func.count(JobRequirement.id))
        .where(JobRequirement.job_id.in_(job_ids))
        .group_by(JobRequirement.job_id)
    )
    return {job_id: int(n) for job_id, n in db.execute(stmt)}


def count(db: Session, user_id: uuid.UUID) -> int:
    return int(db.scalar(select(func.count(JobDescription.id)).where(JobDescription.user_id == user_id)) or 0)
