from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class DimensionOut(BaseModel):
    score: float | None
    weight: float
    effective_weight: float | None
    contribution: float
    label: str
    explanation: str


class AnalysisSummaryOut(BaseModel):
    id: uuid.UUID
    resume_id: uuid.UUID
    resume_name: str
    resume_version: int
    job_id: uuid.UUID
    job_title: str
    company: str | None
    overall_score: float
    status: str
    engine_version: str
    dimension_scores: dict[str, DimensionOut]
    created_at: datetime


class ScoringConfigOut(BaseModel):
    weights: dict[str, float]
    formula: str


class AnalysisDetailOut(AnalysisSummaryOut):
    disclaimer: str
    scoring_config: ScoringConfigOut
    metrics: dict[str, float | None]
    keyword_counts: dict[str, int]
    skills_comparison: list[dict[str, Any]]
    section_analysis: list[dict[str, Any]]


class AnalysisCreate(BaseModel):
    resume_id: uuid.UUID
    job_id: uuid.UUID
    scoring_weights: dict[str, float] | None = Field(default=None)


class KeywordMatchOut(ORMModel):
    id: uuid.UUID
    requirement_id: uuid.UUID | None
    original_keyword: str
    normalized_keyword: str
    kind: str
    importance: str
    category: str
    match_type: str
    result_category: str
    similarity: float
    confidence: float
    credit: float
    occurrences: int
    evidence_level: str | None
    source_section: str | None
    suggested_section: str | None
    explanation: str


class RecommendationOut(ORMModel):
    id: uuid.UUID
    section_type: str
    priority: str
    kind: str
    title: str
    detail: str
    related_keyword: str | None
    is_suggestion: bool
    caveat: str | None
    example_template: str | None


class CompareOut(BaseModel):
    a: AnalysisSummaryOut
    b: AnalysisSummaryOut
    score_delta: float
    dimension_deltas: dict[str, float | None]
    improved_keywords: list[str]
    regressed_keywords: list[str]
    unchanged_missing: list[str]


class TrendPoint(BaseModel):
    analysis_id: uuid.UUID
    resume_id: uuid.UUID
    resume_name: str
    resume_version: int
    overall_score: float
    created_at: datetime
