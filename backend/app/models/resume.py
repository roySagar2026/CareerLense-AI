from __future__ import annotations

import uuid

from sqlalchemy import JSON, Boolean, Float, ForeignKey, Index, Integer, LargeBinary, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, IdMixin, TimestampMixin


class Resume(IdMixin, TimestampMixin, Base):
    __tablename__ = "resumes"
    __table_args__ = (
        Index("ix_resumes_user_created", "user_id", "created_at"),
        Index("ix_resumes_user_sha", "user_id", "sha256"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(200))
    version: Mapped[int] = mapped_column(Integer, default=1)
    parent_resume_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("resumes.id", ondelete="SET NULL"))
    original_filename: Mapped[str] = mapped_column(String(255))
    mime_type: Mapped[str] = mapped_column(String(100))
    size_bytes: Mapped[int] = mapped_column(Integer)
    sha256: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(20), default="ready")
    has_original_file: Mapped[bool] = mapped_column(Boolean, default=False)
    extraction_method: Mapped[str | None] = mapped_column(String(20))
    extraction_confidence: Mapped[float | None] = mapped_column(Float)
    page_count: Mapped[int | None] = mapped_column(Integer)
    word_count: Mapped[int] = mapped_column(Integer, default=0)
    raw_text: Mapped[str] = mapped_column(Text, default="")
    parsed_data: Mapped[dict] = mapped_column(JSON, default=dict)
    warnings: Mapped[list] = mapped_column(JSON, default=list)
    error_message: Mapped[str | None] = mapped_column(Text)

    sections: Mapped[list[ResumeSection]] = relationship(
        back_populates="resume",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="ResumeSection.order_index",
    )
    skills: Mapped[list[ExtractedSkill]] = relationship(
        back_populates="resume", cascade="all, delete-orphan", passive_deletes=True
    )
    file: Mapped[ResumeFile | None] = relationship(
        back_populates="resume", uselist=False, cascade="all, delete-orphan", passive_deletes=True
    )


class ResumeFile(Base):
    """Original upload bytes, kept apart from the resume row so list queries stay light."""

    __tablename__ = "resume_files"

    resume_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("resumes.id", ondelete="CASCADE"), primary_key=True)
    content: Mapped[bytes] = mapped_column(LargeBinary)

    resume: Mapped[Resume] = relationship(back_populates="file")


class ResumeSection(IdMixin, Base):
    __tablename__ = "resume_sections"

    resume_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("resumes.id", ondelete="CASCADE"), index=True)
    section_type: Mapped[str] = mapped_column(String(30))
    heading_text: Mapped[str | None] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text, default="")
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    page_start: Mapped[int | None] = mapped_column(Integer)
    confidence: Mapped[float] = mapped_column(Float, default=0.8)
    user_edited: Mapped[bool] = mapped_column(Boolean, default=False)

    resume: Mapped[Resume] = relationship(back_populates="sections")


class ExtractedSkill(IdMixin, Base):
    __tablename__ = "extracted_skills"

    resume_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("resumes.id", ondelete="CASCADE"), index=True)
    canonical_name: Mapped[str] = mapped_column(String(120))
    surface_form: Mapped[str] = mapped_column(String(120))
    category: Mapped[str] = mapped_column(String(30))
    section_type: Mapped[str | None] = mapped_column(String(30))
    context_snippet: Mapped[str | None] = mapped_column(Text)
    evidence_level: Mapped[str] = mapped_column(String(20))
    occurrences: Mapped[int] = mapped_column(Integer, default=1)

    resume: Mapped[Resume] = relationship(back_populates="skills")
