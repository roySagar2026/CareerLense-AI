from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import User
from app.repositories import jobs as jobs_repo
from app.schemas.common import Page, PageParams
from app.schemas.job import JobCreate, JobDetailOut, JobImportUrl, JobOut, JobUpdate
from app.services import job_service

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("", response_model=JobDetailOut, status_code=201)
def create_job(body: JobCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    job = job_service.create(db, user, body)
    db.commit()
    return job_service.to_detail(job)


@router.post("/import-url", response_model=JobDetailOut, status_code=201)
def import_job_url(body: JobImportUrl, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    job = job_service.import_url(db, user, body)
    db.commit()
    return job_service.to_detail(job)


@router.get("", response_model=Page[JobOut])
def list_jobs(
    search: str | None = Query(default=None, max_length=100),
    paging: PageParams = Depends(),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows, total = jobs_repo.list_page(db, user.id, search, paging.offset, paging.page_size)
    counts = jobs_repo.requirement_counts(db, [r.id for r in rows])
    items = [job_service.to_out(r, counts.get(r.id, 0)) for r in rows]
    return Page(items=items, total=total, page=paging.page, page_size=paging.page_size)


@router.get("/{job_id}", response_model=JobDetailOut)
def get_job(job_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return job_service.to_detail(job_service.get(db, user, job_id))


@router.patch("/{job_id}", response_model=JobDetailOut)
def update_job(
    job_id: uuid.UUID, body: JobUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    job = job_service.update(db, user, job_id, body)
    db.commit()
    db.refresh(job)
    return job_service.to_detail(job)


@router.delete("/{job_id}", status_code=204)
def delete_job(job_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    job_service.delete(db, user, job_id)
    db.commit()
    return Response(status_code=204)
