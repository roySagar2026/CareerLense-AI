"""User, token and audit queries."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import Select, func, or_, select, update
from sqlalchemy.orm import Session, joinedload

from app.models import AuditLog, PasswordResetToken, RefreshToken, User, UserProfile


def get_by_email(db: Session, email: str) -> User | None:
    stmt = select(User).options(joinedload(User.profile)).where(User.email == email.lower())
    return db.scalars(stmt).first()


def get_by_id(db: Session, user_id: uuid.UUID) -> User | None:
    stmt = select(User).options(joinedload(User.profile)).where(User.id == user_id)
    return db.scalars(stmt).first()


def create_user(db: Session, email: str, password_hash: str, full_name: str | None) -> User:
    user = User(email=email.lower(), password_hash=password_hash)
    user.profile = UserProfile(full_name=full_name)
    db.add(user)
    db.flush()
    return user


# ------------------------------------------------------------- refresh tokens
def add_refresh_token(
    db: Session, user_id: uuid.UUID, token_hash: str, family_id: uuid.UUID, expires_at: datetime
) -> RefreshToken:
    row = RefreshToken(user_id=user_id, token_hash=token_hash, family_id=family_id, expires_at=expires_at)
    db.add(row)
    db.flush()
    return row


def get_refresh_token(db: Session, token_hash: str) -> RefreshToken | None:
    return db.scalars(select(RefreshToken).where(RefreshToken.token_hash == token_hash)).first()


def revoke_family(db: Session, family_id: uuid.UUID) -> None:
    db.execute(
        update(RefreshToken)
        .where(RefreshToken.family_id == family_id, RefreshToken.revoked_at.is_(None))
        .values(revoked_at=datetime.now(UTC))
    )


def revoke_all_for_user(db: Session, user_id: uuid.UUID) -> None:
    db.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
        .values(revoked_at=datetime.now(UTC))
    )


# --------------------------------------------------------------- reset tokens
def add_reset_token(db: Session, user_id: uuid.UUID, token_hash: str, expires_at: datetime) -> None:
    db.execute(
        update(PasswordResetToken)
        .where(PasswordResetToken.user_id == user_id, PasswordResetToken.used_at.is_(None))
        .values(used_at=datetime.now(UTC))
    )
    db.add(PasswordResetToken(user_id=user_id, token_hash=token_hash, expires_at=expires_at))
    db.flush()


def get_reset_token(db: Session, token_hash: str) -> PasswordResetToken | None:
    return db.scalars(select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash)).first()


# ---------------------------------------------------------------------- audit
def add_audit(db: Session, **fields: object) -> None:
    db.add(AuditLog(**fields))


def count_recent_failures(db: Session, ip_hash: str | None, email_hash: str, window_minutes: int) -> int:
    since = datetime.now(UTC) - timedelta(minutes=window_minutes)
    conditions = [AuditLog.resource_id == email_hash]
    if ip_hash:
        conditions.append(AuditLog.ip_hash == ip_hash)
    stmt: Select = select(func.count(AuditLog.id)).where(
        AuditLog.action == "login_failed", AuditLog.created_at >= since, or_(*conditions)
    )
    return int(db.scalar(stmt) or 0)


def recent_activity(db: Session, user_id: uuid.UUID, limit: int) -> list[AuditLog]:
    stmt = (
        select(AuditLog)
        .where(AuditLog.user_id == user_id, AuditLog.action.notin_(["login_failed", "token_refresh"]))
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
    )
    return list(db.scalars(stmt))


def count_recent_by_ip(db: Session, ip_hash: str | None, action: str, window_minutes: int) -> int:
    if not ip_hash:
        return 0
    since = datetime.now(UTC) - timedelta(minutes=window_minutes)
    stmt = select(func.count(AuditLog.id)).where(
        AuditLog.action == action, AuditLog.ip_hash == ip_hash, AuditLog.created_at >= since
    )
    return int(db.scalar(stmt) or 0)
