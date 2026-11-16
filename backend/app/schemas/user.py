from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.core.security import validate_password_strength
from app.schemas.common import ORMModel


class PrivacySettings(BaseModel):
    retention_days: int | None = Field(default=None, ge=1, le=3650)
    store_original_files: bool = True


class UserOut(ORMModel):
    id: uuid.UUID
    email: str
    full_name: str | None
    headline: str | None
    created_at: datetime
    privacy_settings: PrivacySettings


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, max_length=120)
    headline: str | None = Field(default=None, max_length=200)
    privacy_settings: PrivacySettings | None = None


def _check_password(value: str) -> str:
    error = validate_password_strength(value)
    if error:
        raise ValueError(error)
    return value


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = Field(default=None, max_length=120)

    _pw = field_validator("password")(_check_password)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=20, max_length=200)
    new_password: str

    _pw = field_validator("new_password")(_check_password)


class PasswordChangeRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str

    _pw = field_validator("new_password")(_check_password)


class DeleteAccountRequest(BaseModel):
    password: str = Field(min_length=1, max_length=128)


class AuthResponse(BaseModel):
    user: UserOut
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int
