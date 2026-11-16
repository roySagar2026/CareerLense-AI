from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel

SECTION_TYPES = (
    "summary",
    "skills",
    "experience",
    "projects",
    "education",
    "certifications",
    "achievements",
    "contact",
    "other",
)


class ResumeOut(ORMModel):
    id: uuid.UUID
    name: str
    version: int
    parent_resume_id: uuid.UUID | None
    original_filename: str
    mime_type: str
    size_bytes: int
    status: str
    extraction_method: str | None
    extraction_confidence: float | None
    page_count: int | None
    word_count: int
    error_message: str | None
    has_original_file: bool = False
    created_at: datetime
    updated_at: datetime


class ResumeSectionOut(ORMModel):
    id: uuid.UUID
    section_type: str
    heading_text: str | None
    content: str
    order_index: int
    page_start: int | None
    confidence: float
    user_edited: bool


class ExtractedSkillOut(ORMModel):
    id: uuid.UUID
    canonical_name: str
    surface_form: str
    category: str
    section_type: str | None
    context_snippet: str | None
    evidence_level: str
    occurrences: int


class ResumeDetailOut(ResumeOut):
    sections: list[ResumeSectionOut]
    skills: list[ExtractedSkillOut]
    parsed_data: dict[str, Any]
    raw_text: str
    warnings: list[str]


class ResumeRename(BaseModel):
    name: str = Field(min_length=1, max_length=200)


class SectionUpdate(BaseModel):
    section_type: str | None = None
    heading_text: str | None = Field(default=None, max_length=200)
    content: str | None = Field(default=None, max_length=30000)
