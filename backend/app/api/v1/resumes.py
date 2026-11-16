from __future__ import annotations

import uuid
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, Form, Query, Request, Response, UploadFile
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session

from app.api.deps import client_ip, get_current_user
from app.core.config import get_settings
from app.core.database import get_db
from app.core.errors import AppError
from app.models import User
from app.repositories import resumes as resumes_repo
from app.schemas.common import Page, PageParams
from app.schemas.resume import ResumeDetailOut, ResumeOut, ResumeRename, SectionUpdate
from app.services import resume_service

router = APIRouter(prefix="/resumes", tags=["resumes"])


@router.post("/upload", response_model=ResumeDetailOut, status_code=201)
async def upload_resume(
    request: Request,
    file: UploadFile = File(...),
    name: str | None = Form(default=None),
    parent_resume_id: str | None = Form(default=None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    limit = get_settings().max_upload_bytes
    data = await file.read(limit + 1)  # never buffer more than limit+1 bytes
    parent_id = None
    if parent_resume_id:
        try:
            parent_id = uuid.UUID(parent_resume_id)
        except ValueError as exc:
            raise AppError(422, "validation_error", "parent_resume_id is not a valid id.") from exc

    def work() -> ResumeDetailOut:
        resume = resume_service.upload(
            db, user, filename=file.filename, data=data, name=name, parent_resume_id=parent_id, ip=client_ip(request)
        )
        db.commit()
        db.refresh(resume)
        return resume_service.to_detail(resume)

    return await run_in_threadpool(work)


@router.get("", response_model=Page[ResumeOut])
def list_resumes(
    search: str | None = Query(default=None, max_length=100),
    paging: PageParams = Depends(),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows, total = resumes_repo.list_page(db, user.id, search, paging.offset, paging.page_size)
    return Page(
        items=[resume_service.to_out(r) for r in rows], total=total, page=paging.page, page_size=paging.page_size
    )


@router.get("/{resume_id}", response_model=ResumeDetailOut)
def get_resume(resume_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    resume = resumes_repo.get_owned(db, user.id, resume_id, detail=True)
    if resume is None:
        raise AppError(404, "not_found", "Resume not found.")
    return resume_service.to_detail(resume)


@router.patch("/{resume_id}", response_model=ResumeOut)
def rename_resume(
    resume_id: uuid.UUID, body: ResumeRename, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    resume = resume_service.rename(db, user, resume_id, body.name)
    db.commit()
    return resume_service.to_out(resume)


@router.patch("/{resume_id}/sections/{section_id}", response_model=ResumeDetailOut)
def update_section(
    resume_id: uuid.UUID,
    section_id: uuid.UUID,
    body: SectionUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    resume = resume_service.update_section(db, user, resume_id, section_id, body)
    db.commit()
    db.refresh(resume)
    return resume_service.to_detail(resume)


@router.post("/{resume_id}/reprocess", response_model=ResumeDetailOut)
def reprocess_resume(resume_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    resume = resume_service.reprocess(db, user, resume_id)
    db.commit()
    db.refresh(resume)
    return resume_service.to_detail(resume)


@router.get("/{resume_id}/versions", response_model=list[ResumeOut])
def resume_versions(resume_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return [resume_service.to_out(r) for r in resume_service.versions(db, user, resume_id)]


@router.get("/{resume_id}/file")
def download_file(resume_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    content, filename, mime = resume_service.get_file(db, user, resume_id)
    return Response(
        content=content,
        media_type=mime,
        headers={
            "Content-Disposition": f"inline; filename*=UTF-8''{quote(filename)}",
            "Cache-Control": "private, no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.delete("/{resume_id}", status_code=204)
def delete_resume(resume_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    resume_service.delete(db, user, resume_id)
    db.commit()
    return Response(status_code=204)
