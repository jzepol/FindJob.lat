"""Cookies de sesión httpOnly."""

from __future__ import annotations

from fastapi import Response

from app.core.config import settings

AUTH_COOKIE = "findjob_session"


def _cookie_domain() -> str | None:
    if settings.is_development:
        return None
    return settings.cookie_domain or None


def set_auth_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=AUTH_COOKIE,
        value=token,
        httponly=True,
        secure=not settings.is_development,
        samesite="lax",
        domain=_cookie_domain(),
        max_age=settings.jwt_access_token_expire_minutes * 60,
        path="/",
    )


def clear_auth_cookie(response: Response) -> None:
    response.delete_cookie(
        key=AUTH_COOKIE,
        domain=_cookie_domain(),
        path="/",
    )