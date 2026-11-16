from __future__ import annotations

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.security import hash_password, verify_password
from app.models import Analysis, JobDescription, Resume, User
from app.models.user import DEFAULT_PRIVACY
from app.repositories import users as users_repo
from app.schemas.user import PasswordChangeRequest, UserOut, UserUpdate
from app.services import audit


def to_out(user: User) -> UserOut:
    profile = user.profile
    privacy = {**DEFAULT_PRIVACY, **(profile.privacy_settings if profile and profile.privacy_settings else {})}
    return UserOut(
        id=user.id,
        email=user.email,
        full_name=profile.full_name if profile else None,
        headline=profile.headline if profile else None,
        created_at=user.created_at,
        privacy_settings=privacy,  # type: ignore[arg-type]
    )


def update_profile(db: Session, user: User, data: UserUpdate) -> User:
    profile = user.profile
    fields = data.model_dump(exclude_unset=True)
    if "full_name" in fields:
        profile.full_name = (fields["full_name"] or "").strip() or None
    if "headline" in fields:
        profile.headline = (fields["headline"] or "").strip() or None
    if data.privacy_settings is not None:
        profile.privacy_settings = data.privacy_settings.model_dump()
    audit.record(db, user.id, "profile_update", resource_type="user", resource_id=user.id, label="Updated profile")
    return user


def change_password(db: Session, user: User, data: PasswordChangeRequest, ip: str | None) -> None:
    if not verify_password(data.current_password, user.password_hash):
        raise AppError(403, "forbidden", "Your current password is incorrect.")
    user.password_hash = hash_password(data.new_password)
    users_repo.revoke_all_for_user(db, user.id)
    audit.record(
        db, user.id, "password_change", resource_type="user", resource_id=user.id, ip=ip, label="Changed password"
    )


def delete_all_data(db: Session, user: User) -> None:
    """Remove resumes, jobs and analyses; keep the account. Children go via ON DELETE CASCADE."""
    db.execute(delete(Analysis).where(Analysis.user_id == user.id))
    db.execute(delete(Resume).where(Resume.user_id == user.id))
    db.execute(delete(JobDescription).where(JobDescription.user_id == user.id))
    audit.record(
        db,
        user.id,
        "data_deleted",
        resource_type="user",
        resource_id=user.id,
        label="Deleted all resumes, jobs and analyses",
    )


def delete_account(db: Session, user: User, password: str) -> None:
    if not verify_password(password, user.password_hash):
        raise AppError(403, "forbidden", "Password is incorrect.")
    delete_all_data(db, user)
    db.delete(user)
