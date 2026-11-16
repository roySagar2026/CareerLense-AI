"""Job description CRUD, parsing into requirements and safe URL import."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.core.errors import AppError, not_found
from app.models import JobDescription, JobRequirement, User
from app.nlp.job_parser import parse_job
from app.repositories import jobs as jobs_repo
from app.schemas.job import JobCreate, JobDetailOut, JobImportUrl, JobOut, JobUpdate
from app.services import audit
from app.utils.html_text import extract_page
from app.utils.url_safety import fetch_public_page

MIN_TEXT = 80


def to_out(job: JobDescription, requirements_count: int) -> JobOut:
    out = JobOut.model_validate(job)
    out.requirements_count = requirements_count
    return out


def to_detail(job: JobDescription) -> JobDetailOut:
    out = JobDetailOut.model_validate(job)
    out.requirements_count = len(job.requirements)
    return out


def _replace_requirements(job: JobDescription) -> None:
    parsed = parse_job(job.raw_text)
    job.requirements.clear()
    for index, req in enumerate(parsed.requirements):
        job.requirements.append(
            JobRequirement(
                kind=req.kind,
                canonical_name=req.canonical_name,
                surface_form=req.surface_form,
                importance=req.importance,
                category=req.category,
                evidence_snippet=req.evidence_snippet,
                min_years=req.min_years,
                order_index=index,
            )
        )


def _clean(value: str | None) -> str | None:
    return (value or "").strip() or None


def create(
    db: Session, user: User, data: JobCreate, *, source_type: str = "paste", source_url: str | None = None
) -> JobDescription:
    parsed = parse_job(data.raw_text)
    job = JobDescription(
        user_id=user.id,
        title=_clean(data.title) or parsed.title_guess or "Untitled role",
        company=_clean(data.company),
        location=_clean(data.location),
        source_type=source_type,
        source_url=source_url,
        raw_text=data.raw_text.strip(),
    )
    db.add(job)
    _replace_requirements(job)
    db.flush()
    audit.record(db, user.id, "job_create", resource_type="job", resource_id=job.id, label=f"Saved job '{job.title}'")
    return job


def import_url(db: Session, user: User, data: JobImportUrl) -> JobDescription:
    final_url, html = fetch_public_page(str(data.url))
    page = extract_page(html)
    if len(page.text) < MIN_TEXT:
        raise AppError(
            422,
            "no_content",
            "No readable job text was found at that link (the page may need JavaScript or a login). "
            "Paste the job description text instead.",
        )
    create_data = JobCreate(
        title=data.title or page.title,
        company=data.company or page.company,
        location=data.location or page.location,
        raw_text=page.text[:50000],
    )
    return create(db, user, create_data, source_type="url", source_url=final_url[:2048])


def get(db: Session, user: User, job_id: uuid.UUID) -> JobDescription:
    job = jobs_repo.get_owned(db, user.id, job_id, detail=True)
    if job is None:
        raise not_found("Job")
    return job


def update(db: Session, user: User, job_id: uuid.UUID, data: JobUpdate) -> JobDescription:
    job = get(db, user, job_id)
    fields = data.model_dump(exclude_unset=True)
    if fields.get("title"):
        job.title = fields["title"].strip()
    if "company" in fields:
        job.company = _clean(fields["company"])
    if "location" in fields:
        job.location = _clean(fields["location"])
    if fields.get("raw_text") and fields["raw_text"].strip() != job.raw_text:
        job.raw_text = fields["raw_text"].strip()
        _replace_requirements(job)
    audit.record(db, user.id, "job_update", resource_type="job", resource_id=job.id, label=f"Updated job '{job.title}'")
    return job


def delete(db: Session, user: User, job_id: uuid.UUID) -> None:
    job = jobs_repo.get_owned(db, user.id, job_id)
    if job is None:
        raise not_found("Job")
    label = f"Deleted job '{job.title}'"
    db.delete(job)
    audit.record(db, user.id, "job_delete", resource_type="job", resource_id=job_id, label=label)
