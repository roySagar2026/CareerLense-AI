from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl

from app.schemas.common import ORMModel


class RequirementOut(ORMModel):
    id: uuid.UUID
    kind: str
    canonical_name: str
    surface_form: str
    importance: str
    category: str
    evidence_snippet: str | None
    min_years: float | None


class JobOut(ORMModel):
    id: uuid.UUID
    title: str
    company: str | None
    location: str | None
    source_type: str
    source_url: str | None
    requirements_count: int = 0
    created_at: datetime
    updated_at: datetime


class JobDetailOut(JobOut):
    raw_text: str
    requirements: list[RequirementOut]


class JobCreate(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    company: str | None = Field(default=None, max_length=200)
    location: str | None = Field(default=None, max_length=200)
    raw_text: str = Field(min_length=80, max_length=50000)


class JobImportUrl(BaseModel):
    url: HttpUrl
    title: str | None = Field(default=None, max_length=200)
    company: str | None = Field(default=None, max_length=200)
    location: str | None = Field(default=None, max_length=200)


class JobUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    company: str | None = Field(default=None, max_length=200)
    location: str | None = Field(default=None, max_length=200)
    raw_text: str | None = Field(default=None, min_length=80, max_length=50000)
