from __future__ import annotations

from fastapi import Depends, Request, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.errors import AppError
from app.core.security import TokenError, decode_access_token
from app.models import User
from app.repositories import users as users_repo

REFRESH_COOKIE = "cl_refresh"
REFRESH_COOKIE_PATH = "/api/v1/auth"
CSRF_HEADER = "x-requested-with"
CSRF_VALUE = "CareerLens"

_bearer = HTTPBearer(auto_error=False)


def client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise AppError(401, "unauthorized", "Authentication required.")
    try:
        user_id = decode_access_token(credentials.credentials)
    except TokenError as exc:
        raise AppError(401, "unauthorized", "Your session has expired. Please sign in again.") from exc
    user = users_repo.get_by_id(db, user_id)
    if user is None or not user.is_active:
        raise AppError(401, "unauthorized", "Authentication required.")
    return user


def require_csrf_header(request: Request) -> None:
    """Cookie-authenticated endpoints require a custom header, which browsers will not
    attach to cross-site requests without a CORS preflight."""
    if request.headers.get(CSRF_HEADER) != CSRF_VALUE:
        raise AppError(403, "forbidden", "Missing required request header.")


def set_refresh_cookie(response: Response, token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        REFRESH_COOKIE,
        token,
        max_age=settings.refresh_token_days * 86400,
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
        path=REFRESH_COOKIE_PATH,
    )


def clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(REFRESH_COOKIE, path=REFRESH_COOKIE_PATH)
