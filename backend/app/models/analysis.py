from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, IdMixin, utcnow
from app.models.job import JobDescription
from app.models.resume import Resume


class Analysis(IdMixin, Base):
    __tablename__ = "analyses"
    __table_args__ = (
        Index("ix_analyses_user_created", "user_id", "created_at"),
        Index("ix_analyses_job", "job_id"),
        Index("ix_analyses_resume", "resume_id"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    resume_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("resumes.id", ondelete="CASCADE"))
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("job_descriptions.id", ondelete="CASCADE"))
    overall_score: Mapped[float] = mapped_column(Float)
    dimension_scores: Mapped[dict] = mapped_column(JSON)
    scoring_config: Mapped[dict] = mapped_column(JSON)
    metrics: Mapped[dict] = mapped_column(JSON)
    keyword_counts: Mapped[dict] = mapped_column(JSON)
    section_analysis: Mapped[list] = mapped_column(JSON)
    skills_comparison: Mapped[list] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(20), default="completed")
    engine_version: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    resume: Mapped[Resume] = relationship()
    job: Mapped[JobDescription] = relationship()
    matches: Mapped[list[KeywordMatch]] = relationship(
        back_populates="analysis", cascade="all, delete-orphan", passive_deletes=True
    )
    recommendations: Mapped[list[Recommendation]] = relationship(
        back_populates="analysis", cascade="all, delete-orphan", passive_deletes=True
    )


class KeywordMatch(IdMixin, Base):
    __tablename__ = "keyword_matches"

    analysis_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("analyses.id", ondelete="CASCADE"), index=True)
    requirement_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("job_requirements.id", ondelete="SET NULL"))
    original_keyword: Mapped[str] = mapped_column(String(300))
    normalized_keyword: Mapped[str] = mapped_column(String(300))
    kind: Mapped[str] = mapped_column(String(20))
    importance: Mapped[str] = mapped_column(String(15))
    category: Mapped[str] = mapped_column(String(30))
    match_type: Mapped[str] = mapped_column(String(15))
    result_category: Mapped[str] = mapped_column(String(25), index=True)
    similarity: Mapped[float] = mapped_column(Float, default=0.0)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    credit: Mapped[float] = mapped_column(Float, default=0.0)
    occurrences: Mapped[int] = mapped_column(Integer, default=0)
    evidence_level: Mapped[str | None] = mapped_column(String(20))
    source_section: Mapped[str | None] = mapped_column(String(30))
    suggested_section: Mapped[str | None] = mapped_column(String(30))
    explanation: Mapped[str] = mapped_column(Text, default="")
    order_index: Mapped[int] = mapped_column(Integer, default=0)

    analysis: Mapped[Analysis] = relationship(back_populates="matches")


class Recommendation(IdMixin, Base):
    __tablename__ = "recommendations"

    analysis_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("analyses.id", ondelete="CASCADE"), index=True)
    section_type: Mapped[str] = mapped_column(String(30))
    priority: Mapped[str] = mapped_column(String(10))
    kind: Mapped[str] = mapped_column(String(25))
    title: Mapped[str] = mapped_column(String(300))
    detail: Mapped[str] = mapped_column(Text)
    related_keyword: Mapped[str | None] = mapped_column(String(300))
    is_suggestion: Mapped[bool] = mapped_column(Boolean, default=True)
    caveat: Mapped[str | None] = mapped_column(Text)
    example_template: Mapped[str | None] = mapped_column(Text)
    order_index: Mapped[int] = mapped_column(Integer, default=0)

    analysis: Mapped[Analysis] = relationship(back_populates="recommendations")
