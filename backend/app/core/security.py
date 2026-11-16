"""Password hashing, JWT access tokens and opaque refresh/reset tokens."""

from __future__ import annotations

import hashlib
import re
import secrets
import uuid
from datetime import UTC, datetime, timedelta

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from app.core.config import get_settings

_hasher = PasswordHasher()
ALGORITHM = "HS256"
PASSWORD_MIN, PASSWORD_MAX = 10, 128
_COMMON = {"password123", "1234567890", "qwertyuiop", "password1234", "letmein1234", "iloveyou123"}


class TokenError(Exception):
    """Access token is missing, malformed or expired."""


def validate_password_strength(password: str) -> str | None:
    """Return an error message, or None when the password meets the policy."""
    if not PASSWORD_MIN <= len(password) <= PASSWORD_MAX:
        return f"Password must be {PASSWORD_MIN}-{PASSWORD_MAX} characters long."
    if not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
        return "Password must contain at least one letter and one digit."
    if password.lower() in _COMMON:
        return "That password is too common."
    return None


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except (VerificationError, InvalidHashError):
        return False


def needs_rehash(password_hash: str) -> bool:
    return _hasher.check_needs_rehash(password_hash)


def create_access_token(user_id: uuid.UUID) -> tuple[str, int]:
    settings = get_settings()
    now = datetime.now(UTC)
    expires = timedelta(minutes=settings.access_token_minutes)
    payload = {"sub": str(user_id), "type": "access", "iat": now, "exp": now + expires, "jti": secrets.token_hex(8)}
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM), int(expires.total_seconds())


def decode_access_token(token: str) -> uuid.UUID:
    try:
        payload = jwt.decode(
            token, get_settings().jwt_secret, algorithms=[ALGORITHM], options={"require": ["exp", "sub"]}
        )
        if payload.get("type") != "access":
            raise TokenError("Wrong token type")
        return uuid.UUID(payload["sub"])
    except (jwt.PyJWTError, ValueError) as exc:
        raise TokenError("Invalid or expired token") from exc


def generate_opaque_token() -> str:
    return secrets.token_urlsafe(48)


def hash_token(token: str) -> str:
    """Refresh and reset tokens are stored only as SHA-256 hashes."""
    return hashlib.sha256(token.encode()).hexdigest()
