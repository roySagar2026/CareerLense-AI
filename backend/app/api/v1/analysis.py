from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.orm import Session

from app.api.deps import client_ip, get_current_user
from app.core.database import get_db
from app.models import User
from app.repositories import analyses as analyses_repo
from app.schemas.analysis import (
    AnalysisCreate,
    AnalysisDetailOut,
    AnalysisSummaryOut,
    CompareOut,
    KeywordMatchOut,
    RecommendationOut,
    TrendPoint,
)
from app.schemas.common import Page, PageParams
from app.services import analysis_service

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post("", response_model=AnalysisDetailOut, status_code=201)
def create_analysis(
    body: AnalysisCreate, request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    analysis = analysis_service.create(db, user, body, client_ip(request))
    db.commit()
    return analysis_service.to_detail(analysis)


@router.get("", response_model=Page[AnalysisSummaryOut])
def list_analyses(
    company: str | None = Query(default=None, max_length=100),
    job_title: str | None = Query(default=None, max_length=100),
    resume_id: uuid.UUID | None = None,
    job_id: uuid.UUID | None = None,
    paging: PageParams = Depends(),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows, total = analyses_repo.list_page(
        db,
        user.id,
        company=company,
        job_title=job_title,
        resume_id=resume_id,
        job_id=job_id,
        offset=paging.offset,
        limit=paging.page_size,
    )
    return Page(
        items=[analysis_service.to_summary(a) for a in rows], total=total, page=paging.page, page_size=paging.page_size
    )


# Fixed paths must be declared before "/{analysis_id}".
@router.get("/compare", response_model=CompareOut)
def compare_analyses(a: uuid.UUID, b: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return analysis_service.compare(db, user, a, b)


@router.get("/trend", response_model=list[TrendPoint])
def score_trend(job_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return analysis_service.trend(db, user, job_id)


@router.get("/{analysis_id}", response_model=AnalysisDetailOut)
def get_analysis(analysis_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return analysis_service.to_detail(analysis_service.get(db, user, analysis_id))


@router.delete("/{analysis_id}", status_code=204)
def delete_analysis(analysis_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    analysis_service.delete(db, user, analysis_id)
    db.commit()
    return Response(status_code=204)


@router.get("/{analysis_id}/keywords", response_model=Page[KeywordMatchOut])
def analysis_keywords(
    analysis_id: uuid.UUID,
    result_category: str | None = None,
    kind: str | None = None,
    importance: str | None = None,
    search: str | None = Query(default=None, max_length=100),
    paging: PageParams = Depends(),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    analysis_service.get(db, user, analysis_id)  # ownership check
    rows, total = analyses_repo.keyword_page(
        db,
        analysis_id,
        filters={"result_category": result_category, "kind": kind, "importance": importance},
        search=search,
        offset=paging.offset,
        limit=paging.page_size,
    )
    return Page(
        items=[KeywordMatchOut.model_validate(r) for r in rows],
        total=total,
        page=paging.page,
        page_size=paging.page_size,
    )


@router.get("/{analysis_id}/recommendations", response_model=list[RecommendationOut])
def analysis_recommendations(
    analysis_id: uuid.UUID,
    priority: str | None = None,
    section_type: str | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    analysis_service.get(db, user, analysis_id)
    return analyses_repo.recommendations(db, analysis_id, priority, section_type)
