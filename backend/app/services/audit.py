from __future__ import annotations

import hashlib
import uuid

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.repositories import users as users_repo


def hash_value(value: str | None) -> str | None:
    """Keyed hash so raw IPs / emails are never stored in the audit log."""
    if not value:
        return None
    return hashlib.sha256(f"{get_settings().jwt_secret}:{value.lower()}".encode()).hexdigest()[:32]


def record(
    db: Session,
    user_id: uuid.UUID | None,
    action: str,
    *,
    resource_type: str | None = None,
    resource_id: object | None = None,
    label: str | None = None,
    ip: str | None = None,
    meta: dict | None = None,
) -> None:
    users_repo.add_audit(
        db,
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id) if resource_id is not None else None,
        label=(label or action.replace("_", " ").capitalize())[:200],
        ip_hash=hash_value(ip),
        meta=meta,
    )
