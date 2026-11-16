from __future__ import annotations

from fastapi import APIRouter, Cookie, Depends, Request, Response
from sqlalchemy.orm import Session

from app.api.deps import REFRESH_COOKIE, clear_refresh_cookie, client_ip, require_csrf_header, set_refresh_cookie
from app.core.database import get_db
from app.core.errors import AppError
from app.repositories import users as users_repo
from app.schemas.common import MessageResponse
from app.schemas.user import (
    AuthResponse,
    ForgotPasswordRequest,
    LoginRequest,
    RegisterRequest,
    ResetPasswordRequest,
)
from app.services import audit, auth_service, user_service

router = APIRouter(prefix="/auth", tags=["auth"])

_REGISTER_PER_HOUR = 10


@router.post("/register", response_model=AuthResponse, status_code=201)
def register(body: RegisterRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    ip = client_ip(request)
    if users_repo.count_recent_by_ip(db, audit.hash_value(ip), "register", 60) >= _REGISTER_PER_HOUR:
        raise AppError(429, "rate_limited", "Too many sign-ups from this network. Try again later.")
    user = auth_service.register(db, body.email, body.password, body.full_name, ip)
    access, expires_in, refresh = auth_service.issue_tokens(db, user)
    db.commit()
    set_refresh_cookie(response, refresh)
    return AuthResponse(user=user_service.to_out(user), access_token=access, expires_in=expires_in)


@router.post("/login", response_model=AuthResponse)
def login(body: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    user = auth_service.login(db, body.email, body.password, client_ip(request))
    access, expires_in, refresh = auth_service.issue_tokens(db, user)
    db.commit()
    set_refresh_cookie(response, refresh)
    return AuthResponse(user=user_service.to_out(user), access_token=access, expires_in=expires_in)


@router.post("/refresh", response_model=AuthResponse, dependencies=[Depends(require_csrf_header)])
def refresh(
    response: Response,
    db: Session = Depends(get_db),
    refresh_cookie: str | None = Cookie(default=None, alias=REFRESH_COOKIE),
):
    try:
        user, access, expires_in, new_refresh = auth_service.refresh(db, refresh_cookie)
    except AppError:
        clear_refresh_cookie(response)
        raise
    db.commit()
    set_refresh_cookie(response, new_refresh)
    return AuthResponse(user=user_service.to_out(user), access_token=access, expires_in=expires_in)


@router.post("/logout", status_code=204, dependencies=[Depends(require_csrf_header)])
def logout(
    db: Session = Depends(get_db),
    refresh_cookie: str | None = Cookie(default=None, alias=REFRESH_COOKIE),
):
    auth_service.logout(db, refresh_cookie)
    db.commit()
    response = Response(status_code=204)
    clear_refresh_cookie(response)
    return response


@router.post("/forgot-password", response_model=MessageResponse, status_code=202)
def forgot_password(body: ForgotPasswordRequest, request: Request, db: Session = Depends(get_db)):
    ip = client_ip(request)
    if users_repo.count_recent_by_ip(db, audit.hash_value(ip), "password_reset_requested", 60) >= 5:
        raise AppError(429, "rate_limited", "Too many reset requests. Try again later.")
    auth_service.forgot_password(db, body.email, ip)
    db.commit()
    return MessageResponse(message="If an account exists for that email, a reset link has been sent.")


@router.post("/reset-password", response_model=MessageResponse)
def reset_password(body: ResetPasswordRequest, request: Request, db: Session = Depends(get_db)):
    auth_service.reset_password(db, body.token, body.new_password, client_ip(request))
    db.commit()
    return MessageResponse(message="Password updated. You can now sign in.")
