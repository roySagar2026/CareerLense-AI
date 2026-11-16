from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.schemas.analysis import AnalysisSummaryOut


class BestResumeOut(BaseModel):
    id: uuid.UUID
    name: str
    version: int
    average_score: float
    analyses_count: int


class ScorePoint(BaseModel):
    date: str
    score: float


class DashboardSummaryOut(BaseModel):
    total_resumes: int
    total_jobs: int
    total_analyses: int
    average_score: float | None
    best_resume: BestResumeOut | None
    recent_analyses: list[AnalysisSummaryOut]
    score_history: list[ScorePoint]


class ActivityOut(BaseModel):
    id: uuid.UUID
    action: str
    resource_type: str | None
    resource_id: str | None
    label: str
    created_at: datetime
