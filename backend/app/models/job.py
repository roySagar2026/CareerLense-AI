from __future__ import annotations

import uuid

from sqlalchemy import Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, IdMixin, TimestampMixin


class JobDescription(IdMixin, TimestampMixin, Base):
    __tablename__ = "job_descriptions"
    __table_args__ = (Index("ix_jobs_user_created", "user_id", "created_at"),)

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(200))
    company: Mapped[str | None] = mapped_column(String(200))
    location: Mapped[str | None] = mapped_column(String(200))
    source_type: Mapped[str] = mapped_column(String(10), default="paste")
    source_url: Mapped[str | None] = mapped_column(String(2048))
    raw_text: Mapped[str] = mapped_column(Text)

    requirements: Mapped[list[JobRequirement]] = relationship(
        back_populates="job",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="JobRequirement.order_index",
    )


class JobRequirement(IdMixin, Base):
    __tablename__ = "job_requirements"

    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("job_descriptions.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(20))
    canonical_name: Mapped[str] = mapped_column(String(300))
    surface_form: Mapped[str] = mapped_column(String(300))
    importance: Mapped[str] = mapped_column(String(15))
    category: Mapped[str] = mapped_column(String(30))
    evidence_snippet: Mapped[str | None] = mapped_column(Text)
    min_years: Mapped[float | None] = mapped_column(Float)
    order_index: Mapped[int] = mapped_column(Integer, default=0)

    job: Mapped[JobDescription] = relationship(back_populates="requirements")
