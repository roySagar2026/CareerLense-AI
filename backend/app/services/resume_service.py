"""Resume upload, (re)processing, section correction and versioning."""

from __future__ import annotations

import hashlib
import uuid

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError, not_found
from app.document_processing.docx_parser import parse_docx
from app.document_processing.models import DocumentParseError, ParsedDocument
from app.document_processing.pdf_parser import parse_pdf
from app.document_processing.section_detector import detect_sections, structure_confidence
from app.models import ExtractedSkill, Resume, ResumeFile, ResumeSection, User
from app.models.user import DEFAULT_PRIVACY
from app.nlp.extractor import ResumeProfile, SectionInput, build_profile
from app.repositories import resumes as resumes_repo
from app.schemas.resume import SECTION_TYPES, ResumeDetailOut, ResumeOut, SectionUpdate
from app.services import audit
from app.utils.files import safe_filename, validate_upload


# ------------------------------------------------------------------ serialisers
def to_out(resume: Resume) -> ResumeOut:
    return ResumeOut.model_validate(resume)


def to_detail(resume: Resume) -> ResumeDetailOut:
    return ResumeDetailOut.model_validate(resume)


# ------------------------------------------------------------------- internals
def _parse(data: bytes, ext: str) -> ParsedDocument:
    if ext == ".pdf":
        return parse_pdf(data, ocr_enabled=get_settings().ocr_enabled)
    return parse_docx(data)


def _replace_derived(resume: Resume, profile: ResumeProfile) -> None:
    resume.raw_text = profile.raw_text
    resume.word_count = profile.word_count
    resume.parsed_data = profile.parsed
    resume.skills.clear()
    for skill in profile.skills.values():
        resume.skills.append(
            ExtractedSkill(
                canonical_name=skill.canonical,
                surface_form=skill.surface_form,
                category=skill.category,
                section_type=skill.section_type,
                context_snippet=skill.snippet,
                evidence_level=skill.evidence_level,
                occurrences=skill.occurrences,
            )
        )


def _apply_parse(resume: Resume, parsed: ParsedDocument) -> None:
    sections = detect_sections(parsed.lines)
    confidence = parsed.extraction_confidence
    if not parsed.needs_ocr:
        confidence = round(min(confidence, 0.5 + 0.5 * structure_confidence(sections)), 2)
    resume.extraction_method = parsed.method
    resume.extraction_confidence = confidence
    resume.page_count = parsed.page_count
    resume.warnings = list(parsed.warnings)
    resume.status = "ready"
    resume.error_message = None

    resume.sections.clear()
    for section in sections:
        resume.sections.append(
            ResumeSection(
                section_type=section.section_type,
                heading_text=section.heading_text,
                content=section.content,
                order_index=section.order_index,
                page_start=section.page_start,
                confidence=section.confidence,
            )
        )
    inputs = [SectionInput(s.section_type, s.heading_text, s.content, s.confidence) for s in sections]
    _replace_derived(resume, build_profile(inputs, confidence))


def _mark_failed(resume: Resume, message: str) -> None:
    resume.status = "failed"
    resume.error_message = message
    resume.extraction_confidence = 0.0
    resume.warnings = []


def _store_original(user: User) -> bool:
    privacy = {**DEFAULT_PRIVACY, **((user.profile.privacy_settings if user.profile else None) or {})}
    return bool(privacy.get("store_original_files", True))


# ------------------------------------------------------------------ public API
def upload(
    db: Session,
    user: User,
    *,
    filename: str | None,
    data: bytes,
    name: str | None,
    parent_resume_id: uuid.UUID | None,
    ip: str | None,
) -> Resume:
    ext, mime = validate_upload(filename, data, get_settings().max_upload_bytes)
    display_name = safe_filename(filename)
    version, parent = 1, None
    if parent_resume_id:
        parent = resumes_repo.get_owned(db, user.id, parent_resume_id)
        if parent is None:
            raise not_found("Parent resume")
        version = parent.version + 1

    resume = Resume(
        user_id=user.id,
        name=(name or "").strip()[:200] or (parent.name if parent else display_name.rsplit(".", 1)[0]),
        version=version,
        parent_resume_id=parent.id if parent else None,
        original_filename=display_name,
        mime_type=mime,
        size_bytes=len(data),
        sha256=hashlib.sha256(data).hexdigest(),
        has_original_file=_store_original(user),
    )
    try:
        _apply_parse(resume, _parse(data, ext))
    except DocumentParseError as exc:
        _mark_failed(resume, str(exc))
    db.add(resume)
    db.flush()
    if resume.has_original_file:
        db.add(ResumeFile(resume_id=resume.id, content=data))
    audit.record(
        db,
        user.id,
        "resume_upload",
        resource_type="resume",
        resource_id=resume.id,
        label=f"Uploaded resume '{resume.name}'",
        ip=ip,
    )
    return resume


def reprocess(db: Session, user: User, resume_id: uuid.UUID) -> Resume:
    resume = resumes_repo.get_owned(db, user.id, resume_id, detail=True)
    if resume is None:
        raise not_found("Resume")
    if resume.file is None:
        raise AppError(
            409, "conflict", "The original file was not stored, so it cannot be reprocessed. Upload it again."
        )
    ext = ".pdf" if resume.mime_type == "application/pdf" else ".docx"
    try:
        _apply_parse(resume, _parse(resume.file.content, ext))
    except DocumentParseError as exc:
        _mark_failed(resume, str(exc))
    audit.record(
        db,
        user.id,
        "resume_reprocess",
        resource_type="resume",
        resource_id=resume.id,
        label=f"Reprocessed resume '{resume.name}'",
    )
    return resume


def rename(db: Session, user: User, resume_id: uuid.UUID, name: str) -> Resume:
    resume = resumes_repo.get_owned(db, user.id, resume_id)
    if resume is None:
        raise not_found("Resume")
    resume.name = name.strip()
    audit.record(
        db,
        user.id,
        "resume_rename",
        resource_type="resume",
        resource_id=resume.id,
        label=f"Renamed resume to '{resume.name}'",
    )
    return resume


def update_section(db: Session, user: User, resume_id: uuid.UUID, section_id: uuid.UUID, data: SectionUpdate) -> Resume:
    resume = resumes_repo.get_owned(db, user.id, resume_id, detail=True)
    if resume is None:
        raise not_found("Resume")
    section = next((s for s in resume.sections if s.id == section_id), None)
    if section is None:
        raise not_found("Section")
    fields = data.model_dump(exclude_unset=True)
    if "section_type" in fields and fields["section_type"] is not None:
        if fields["section_type"] not in SECTION_TYPES:
            raise AppError(422, "validation_error", f"Unknown section type '{fields['section_type']}'.")
        section.section_type = fields["section_type"]
    if "heading_text" in fields:
        section.heading_text = (fields["heading_text"] or "").strip() or None
    if "content" in fields and fields["content"] is not None:
        section.content = fields["content"].strip()
    section.user_edited = True
    section.confidence = 1.0

    ordered = sorted(resume.sections, key=lambda s: s.order_index)
    inputs = [SectionInput(s.section_type, s.heading_text, s.content, s.confidence) for s in ordered]
    _replace_derived(resume, build_profile(inputs, resume.extraction_confidence or 0.8))
    audit.record(
        db,
        user.id,
        "resume_section_edit",
        resource_type="resume",
        resource_id=resume.id,
        label=f"Corrected a section of '{resume.name}'",
    )
    return resume


def versions(db: Session, user: User, resume_id: uuid.UUID) -> list[Resume]:
    """The whole version chain that contains `resume_id`, ordered by version."""
    everything = {r.id: r for r in resumes_repo.all_for_user(db, user.id)}
    if resume_id not in everything:
        raise not_found("Resume")
    root = everything[resume_id]
    seen = {root.id}
    while root.parent_resume_id and root.parent_resume_id in everything and root.parent_resume_id not in seen:
        root = everything[root.parent_resume_id]
        seen.add(root.id)
    chain, frontier = {root.id: root}, [root.id]
    while frontier:
        parent = frontier.pop()
        for candidate in everything.values():
            if candidate.parent_resume_id == parent and candidate.id not in chain:
                chain[candidate.id] = candidate
                frontier.append(candidate.id)
    return sorted(chain.values(), key=lambda r: (r.version, r.created_at))


def get_file(db: Session, user: User, resume_id: uuid.UUID) -> tuple[bytes, str, str]:
    resume = resumes_repo.get_owned(db, user.id, resume_id)
    if resume is None:
        raise not_found("Resume")
    if resume.file is None:
        raise not_found("Original file")
    return resume.file.content, resume.original_filename, resume.mime_type


def delete(db: Session, user: User, resume_id: uuid.UUID) -> None:
    resume = resumes_repo.get_owned(db, user.id, resume_id)
    if resume is None:
        raise not_found("Resume")
    label = f"Deleted resume '{resume.name}'"
    db.delete(resume)
    audit.record(db, user.id, "resume_delete", resource_type="resume", resource_id=resume_id, label=label)
