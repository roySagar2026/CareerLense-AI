"""Transactional email via Resend's HTTP API. Without RESEND_API_KEY nothing is sent."""

from __future__ import annotations

import html
import logging

import httpx

from app.core.config import get_settings

logger = logging.getLogger("careerlens.email")


def email_configured() -> bool:
    return bool(get_settings().resend_api_key)


def send_password_reset(to: str, reset_link: str) -> bool:
    settings = get_settings()
    if not settings.resend_api_key:
        if settings.is_production:
            logger.warning("Password reset requested but no email provider is configured (RESEND_API_KEY).")
        else:
            logger.info("DEV ONLY - password reset link for %s: %s", to, reset_link)
        return False
    safe_link = html.escape(reset_link, quote=True)
    body = (
        "<p>We received a request to reset your CareerLens AI password.</p>"
        f'<p><a href="{safe_link}">Choose a new password</a> (valid for 1 hour).</p>'
        "<p>If you did not ask for this, you can ignore this email.</p>"
    )
    try:
        response = httpx.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {settings.resend_api_key}"},
            json={
                "from": settings.email_from,
                "to": [to],
                "subject": "Reset your CareerLens AI password",
                "html": body,
            },
            timeout=8.0,
        )
        response.raise_for_status()
        return True
    except httpx.HTTPError:
        logger.exception("Failed to send password reset email")
        return False
