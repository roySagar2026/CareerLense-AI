"""Application settings, read from environment variables (and an optional local .env)."""

from __future__ import annotations

from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_DEV_SECRET = "dev-only-insecure-secret-change-me-0123456789abcdef"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "development"  # development | production | test
    database_url: str = "sqlite:///./careerlens.db"
    jwt_secret: str = _DEV_SECRET
    access_token_minutes: int = 15
    refresh_token_days: int = 7
    cors_origins: str = ""  # comma separated; empty = same-origin only
    app_base_url: str = "http://localhost:5173"  # used in password-reset links
    max_upload_mb: int = 4
    resend_api_key: str = ""
    email_from: str = "CareerLens <onboarding@resend.dev>"
    ocr_enabled: bool = False
    llm_provider: str = "none"  # reserved: optional rephrasing provider, unused by default
    llm_api_key: str = ""
    login_max_failures: int = 8
    login_window_minutes: int = 15

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"

    @property
    def sqlalchemy_url(self) -> str:
        url = self.database_url.strip()
        if url.startswith("postgres://"):
            url = "postgresql://" + url[len("postgres://") :]
        if url.startswith("postgresql://"):
            url = "postgresql+psycopg://" + url[len("postgresql://") :]
        return url

    @property
    def cors_list(self) -> list[str]:
        return [o.strip().rstrip("/") for o in self.cors_origins.split(",") if o.strip()]

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024

    @model_validator(mode="after")
    def _check_production_secrets(self) -> Settings:
        if self.is_production and (self.jwt_secret == _DEV_SECRET or len(self.jwt_secret) < 32):
            raise ValueError("JWT_SECRET must be set to a random string of at least 32 characters in production.")
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
