"""JWT y hashing de contraseñas."""

from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings

_used_oauth_codes: set[str] = set()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode()[:72], bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str | None) -> bool:
    if not hashed:
        return False
    return bcrypt.checkpw(plain.encode()[:72], hashed.encode())


def create_access_token(
    subject: UUID | str,
    *,
    extra: dict[str, Any] | None = None,
    expires_minutes: int | None = None,
) -> str:
    expire = datetime.now(UTC) + timedelta(
        minutes=expires_minutes or settings.jwt_access_token_expire_minutes,
    )
    payload: dict[str, Any] = {"sub": str(subject), "exp": expire, "type": "access"}
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def create_oauth_state(provider: str) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=10)
    payload = {"provider": provider, "exp": expire, "type": "oauth_state"}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])


def decode_oauth_state(state: str, provider: str) -> bool:
    try:
        payload = decode_token(state)
        return payload.get("type") == "oauth_state" and payload.get("provider") == provider
    except JWTError:
        return False


def decode_access_token(token: str) -> UUID | None:
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            return None
        return UUID(payload["sub"])
    except (JWTError, KeyError, ValueError):
        return None


def create_oauth_exchange_code(subject: UUID | str) -> str:
    """Código de un solo uso (60s) para intercambiar por sesión sin JWT en la URL."""
    jti = secrets.token_urlsafe(16)
    expire = datetime.now(UTC) + timedelta(seconds=60)
    payload = {
        "sub": str(subject),
        "exp": expire,
        "type": "oauth_code",
        "jti": jti,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def consume_oauth_exchange_code(code: str) -> UUID | None:
    try:
        payload = decode_token(code)
        if payload.get("type") != "oauth_code":
            return None
        jti = payload.get("jti")
        if not jti or jti in _used_oauth_codes:
            return None
        _used_oauth_codes.add(jti)
        if len(_used_oauth_codes) > 10_000:
            _used_oauth_codes.clear()
        return UUID(payload["sub"])
    except (JWTError, KeyError, ValueError):
        return None