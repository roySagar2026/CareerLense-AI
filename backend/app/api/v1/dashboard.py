from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import User
from app.schemas.dashboard import ActivityOut, DashboardSummaryOut
from app.services import dashboard_service

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummaryOut)
def dashboard_summary(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return dashboard_service.summary(db, user)


@router.get("/recent-activity", response_model=list[ActivityOut])
def recent_activity(
    limit: int = Query(10, ge=1, le=50), user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    return dashboard_service.recent_activity(db, user, limit)
