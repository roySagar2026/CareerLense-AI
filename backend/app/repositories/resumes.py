from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models import Resume


def get_owned(db: Session, user_id: uuid.UUID, resume_id: uuid.UUID, *, detail: bool = False) -> Resume | None:
    stmt = select(Resume).where(Resume.id == resume_id, Resume.user_id == user_id)
    if detail:
        stmt = stmt.options(selectinload(Resume.sections), selectinload(Resume.skills))
    return db.scalars(stmt).first()


def list_page(db: Session, user_id: uuid.UUID, search: str | None, offset: int, limit: int) -> tuple[list[Resume], int]:
    base = select(Resume).where(Resume.user_id == user_id)
    if search:
        base = base.where(Resume.name.ilike(f"%{search}%"))
    total = db.scalar(select(func.count()).select_from(base.subquery())) or 0
    rows = db.scalars(base.order_by(Resume.created_at.desc()).offset(offset).limit(limit))
    return list(rows), int(total)


def all_for_user(db: Session, user_id: uuid.UUID) -> list[Resume]:
    return list(db.scalars(select(Resume).where(Resume.user_id == user_id)))


def count(db: Session, user_id: uuid.UUID) -> int:
    return int(db.scalar(select(func.count(Resume.id)).where(Resume.user_id == user_id)) or 0)
