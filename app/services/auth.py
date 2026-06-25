"""Registro, login y vinculación OAuth."""

from __future__ import annotations

import os
import secrets
import uuid

# Dev local: oauthlib exige HTTPS salvo esta variable
os.environ.setdefault("OAUTHLIB_INSECURE_TRANSPORT", "1")

import httpx
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import hash_password
from app.models.base import KarmaEventType, OAuthProvider
from app.models.oauth_account import OAuthAccount
from app.models.profile import Profile
from app.models.user import User
from app.services.karma import award_karma

logger = structlog.get_logger(__name__)


class AuthError(Exception):
    """Error de autenticación."""


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    result = await session.execute(
        select(User)
        .where(User.email == email.lower())
        .options(selectinload(User.profile), selectinload(User.oauth_accounts))
    )
    return result.scalar_one_or_none()


async def get_user_by_id(session: AsyncSession, user_id: uuid.UUID) -> User | None:
    result = await session.execute(
        select(User)
        .where(User.id == user_id)
        .options(selectinload(User.profile), selectinload(User.oauth_accounts))
    )
    return result.scalar_one_or_none()


async def register_user(
    session: AsyncSession,
    *,
    email: str,
    password: str,
    full_name: str | None = None,
) -> User:
    email = email.lower().strip()
    if await get_user_by_email(session, email):
        raise AuthError("El email ya está registrado")

    user = User(
        email=email,
        hashed_password=hash_password(password),
        is_verified=False,
    )
    session.add(user)
    await session.flush()

    profile = Profile(user_id=user.id, full_name=full_name)
    session.add(profile)
    await session.flush()
    await session.refresh(user, ["profile", "oauth_accounts"])
    return user


async def authenticate_user(
    session: AsyncSession,
    email: str,
    password: str,
) -> User:
    user = await get_user_by_email(session, email.lower().strip())
    if user is None or not user.hashed_password:
        raise AuthError("Credenciales inválidas")

    from app.core.security import verify_password

    if not verify_password(password, user.hashed_password):
        raise AuthError("Credenciales inválidas")
    if not user.is_active:
        raise AuthError("Cuenta desactivada")
    return user


async def upsert_oauth_user(
    session: AsyncSession,
    *,
    provider: OAuthProvider,
    provider_user_id: str,
    email: str | None,
    display_name: str | None,
    avatar_url: str | None = None,
) -> User:
    """Crea o vincula usuario vía OAuth."""
    result = await session.execute(
        select(OAuthAccount)
        .where(
            OAuthAccount.provider == provider,
            OAuthAccount.provider_user_id == provider_user_id,
        )
        .options(selectinload(OAuthAccount.user).selectinload(User.profile))
    )
    oauth = result.scalar_one_or_none()

    if oauth is not None:
        user = oauth.user
        oauth.email = email or oauth.email
        oauth.display_name = display_name or oauth.display_name
        oauth.avatar_url = avatar_url or oauth.avatar_url
        await session.flush()
        return user

    user: User | None = None
    if email:
        user = await get_user_by_email(session, email)

    if user is None:
        if not email:
            raise AuthError("OAuth no devolvió email — no se puede crear cuenta")
        user = User(
            email=email.lower(),
            hashed_password=hash_password(secrets.token_urlsafe(32)),
            is_verified=True,
        )
        session.add(user)
        await session.flush()
        profile = Profile(user_id=user.id, full_name=display_name)
        session.add(profile)
        await award_karma(session, user, KarmaEventType.EMAIL_VERIFIED)

    session.add(
        OAuthAccount(
            user_id=user.id,
            provider=provider,
            provider_user_id=provider_user_id,
            email=email,
            display_name=display_name,
            avatar_url=avatar_url,
        )
    )
    await award_karma(session, user, KarmaEventType.OAUTH_LINKED)
    await session.flush()
    await session.refresh(user, ["profile", "oauth_accounts"])
    return user


async def exchange_google_code(code: str) -> dict:
    from app.core.config import settings

    async with httpx.AsyncClient() as client:
        token_res = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": settings.google_redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        if token_res.status_code != 200:
            logger.error("google_token_error", body=token_res.text)
            raise AuthError(f"Google token error: {token_res.text[:200]}")

        tokens = token_res.json()
        access_token = tokens.get("access_token")
        if not access_token:
            raise AuthError("Google no devolvió access_token")

        user_res = await client.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if user_res.status_code != 200:
            logger.error("google_userinfo_error", body=user_res.text)
            raise AuthError(f"Google userinfo error: {user_res.text[:200]}")
        return user_res.json()