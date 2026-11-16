"""Registration, login, refresh-token rotation (with reuse detection) and password reset."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from urllib.parse import quote

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError
from app.core.security import (
    create_access_token,
    generate_opaque_token,
    hash_password,
    hash_token,
    needs_rehash,
    verify_password,
)
from app.models import User
from app.repositories import users as users_repo
from app.services import audit, email_service

_DUMMY_HASH = hash_password("timing-equalisation-placeholder-1")
RESET_TOKEN_HOURS = 1


def _unauthorized(message: str = "Invalid email or password.") -> AppError:
    return AppError(401, "unauthorized", message)


def issue_tokens(db: Session, user: User, family_id: uuid.UUID | None = None) -> tuple[str, int, str]:
    """Return (access_token, expires_in, refresh_token_plaintext)."""
    settings = get_settings()
    access, expires_in = create_access_token(user.id)
    refresh = generate_opaque_token()
    users_repo.add_refresh_token(
        db,
        user.id,
        hash_token(refresh),
        family_id or uuid.uuid4(),
        datetime.now(UTC) + timedelta(days=settings.refresh_token_days),
    )
    return access, expires_in, refresh


def register(db: Session, email: str, password: str, full_name: str | None, ip: str | None) -> User:
    if users_repo.get_by_email(db, email):
        raise AppError(409, "conflict", "An account with this email already exists.")
    user = users_repo.create_user(db, email, hash_password(password), full_name.strip() if full_name else None)
    audit.record(db, user.id, "register", resource_type="user", resource_id=user.id, label="Created account", ip=ip)
    return user


def login(db: Session, email: str, password: str, ip: str | None) -> User:
    settings = get_settings()
    email_hash = audit.hash_value(email) or ""
    failures = users_repo.count_recent_failures(db, audit.hash_value(ip), email_hash, settings.login_window_minutes)
    if failures >= settings.login_max_failures:
        raise AppError(429, "rate_limited", "Too many failed sign-in attempts. Try again in a few minutes.")
    user = users_repo.get_by_email(db, email)
    valid = verify_password(password, user.password_hash if user else _DUMMY_HASH)
    if not user or not valid or not user.is_active:
        audit.record(
            db, user.id if user else None, "login_failed", resource_id=email_hash, ip=ip, label="Failed sign-in"
        )
        db.commit()  # persist the failure even though we raise
        raise _unauthorized()
    if needs_rehash(user.password_hash):
        user.password_hash = hash_password(password)
    audit.record(db, user.id, "login", resource_type="user", resource_id=user.id, label="Signed in", ip=ip)
    return user


def refresh(db: Session, refresh_plain: str | None) -> tuple[User, str, int, str]:
    if not refresh_plain:
        raise _unauthorized("Session expired. Please sign in again.")
    row = users_repo.get_refresh_token(db, hash_token(refresh_plain))
    if row is None:
        raise _unauthorized("Session expired. Please sign in again.")
    if row.revoked_at is not None:
        # A rotated token was presented again: assume theft and kill the whole family.
        users_repo.revoke_family(db, row.family_id)
        db.commit()
        raise _unauthorized("Session expired. Please sign in again.")
    expires = row.expires_at if row.expires_at.tzinfo else row.expires_at.replace(tzinfo=UTC)
    if expires <= datetime.now(UTC):
        raise _unauthorized("Session expired. Please sign in again.")
    user = users_repo.get_by_id(db, row.user_id)
    if user is None or not user.is_active:
        raise _unauthorized("Session expired. Please sign in again.")
    access, expires_in, new_refresh = issue_tokens(db, user, family_id=row.family_id)
    new_row = users_repo.get_refresh_token(db, hash_token(new_refresh))
    row.revoked_at = datetime.now(UTC)
    row.replaced_by = new_row.id if new_row else None
    return user, access, expires_in, new_refresh


def logout(db: Session, refresh_plain: str | None) -> None:
    if not refresh_plain:
        return
    row = users_repo.get_refresh_token(db, hash_token(refresh_plain))
    if row:
        users_repo.revoke_family(db, row.family_id)


def forgot_password(db: Session, email: str, ip: str | None) -> None:
    """Never reveals whether the account exists."""
    user = users_repo.get_by_email(db, email)
    if not user or not user.is_active:
        return
    token = generate_opaque_token()
    users_repo.add_reset_token(db, user.id, hash_token(token), datetime.now(UTC) + timedelta(hours=RESET_TOKEN_HOURS))
    audit.record(
        db,
        user.id,
        "password_reset_requested",
        resource_type="user",
        resource_id=user.id,
        ip=ip,
        label="Requested a password reset",
    )
    db.commit()
    link = f"{get_settings().app_base_url.rstrip('/')}/reset-password?token={quote(token)}"
    email_service.send_password_reset(user.email, link)


def reset_password(db: Session, token: str, new_password: str, ip: str | None) -> None:
    row = users_repo.get_reset_token(db, hash_token(token))
    now = datetime.now(UTC)
    expires = (
        row.expires_at.replace(tzinfo=UTC)
        if row and row.expires_at.tzinfo is None
        else (row.expires_at if row else now)
    )
    if row is None or row.used_at is not None or expires <= now:
        raise AppError(400, "bad_request", "This reset link is invalid or has expired. Request a new one.")
    user = users_repo.get_by_id(db, row.user_id)
    if user is None:
        raise AppError(400, "bad_request", "This reset link is invalid or has expired. Request a new one.")
    user.password_hash = hash_password(new_password)
    row.used_at = now
    users_repo.revoke_all_for_user(db, user.id)
    audit.record(
        db, user.id, "password_reset", resource_type="user", resource_id=user.id, ip=ip, label="Reset password"
    )
