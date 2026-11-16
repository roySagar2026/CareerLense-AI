from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models import Analysis, Resume, User
from app.repositories import jobs as jobs_repo
from app.repositories import resumes as resumes_repo
from app.repositories import users as users_repo
from app.schemas.dashboard import ActivityOut, BestResumeOut, DashboardSummaryOut, ScorePoint
from app.services.analysis_service import to_summary


def summary(db: Session, user: User) -> DashboardSummaryOut:
    total_analyses = int(db.scalar(select(func.count(Analysis.id)).where(Analysis.user_id == user.id)) or 0)
    average = db.scalar(select(func.avg(Analysis.overall_score)).where(Analysis.user_id == user.id))

    best_row = db.execute(
        select(Analysis.resume_id, func.avg(Analysis.overall_score).label("avg"), func.count(Analysis.id))
        .where(Analysis.user_id == user.id)
        .group_by(Analysis.resume_id)
        .order_by(func.avg(Analysis.overall_score).desc())
        .limit(1)
    ).first()
    best = None
    if best_row:
        resume = db.get(Resume, best_row[0])
        if resume:
            best = BestResumeOut(
                id=resume.id,
                name=resume.name,
                version=resume.version,
                average_score=round(float(best_row[1]), 1),
                analyses_count=int(best_row[2]),
            )

    recent = db.scalars(
        select(Analysis)
        .options(joinedload(Analysis.resume), joinedload(Analysis.job))
        .where(Analysis.user_id == user.id)
        .order_by(Analysis.created_at.desc())
        .limit(5)
    ).unique()
    history = db.execute(
        select(Analysis.created_at, Analysis.overall_score)
        .where(Analysis.user_id == user.id)
        .order_by(Analysis.created_at.desc())
        .limit(10)
    ).all()
    return DashboardSummaryOut(
        total_resumes=resumes_repo.count(db, user.id),
        total_jobs=jobs_repo.count(db, user.id),
        total_analyses=total_analyses,
        average_score=round(float(average), 1) if average is not None else None,
        best_resume=best,
        recent_analyses=[to_summary(a) for a in recent],
        score_history=[ScorePoint(date=row[0].date().isoformat(), score=row[1]) for row in reversed(history)],
    )


def recent_activity(db: Session, user: User, limit: int) -> list[ActivityOut]:
    return [
        ActivityOut(
            id=row.id,
            action=row.action,
            resource_type=row.resource_type,
            resource_id=row.resource_id,
            label=row.label or row.action.replace("_", " ").capitalize(),
            created_at=row.created_at,
        )
        for row in users_repo.recent_activity(db, user.id, limit)
    ]
