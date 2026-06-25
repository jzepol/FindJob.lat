"""Autenticación JWT + OAuth Google."""

from __future__ import annotations

from typing import Annotated
from urllib.parse import quote, urlencode

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_session
from app.api.schemas import LoginIn, OAuthAccountOut, ProfileOut, RegisterIn, TokenOut, UserOut
from app.core.config import settings
from app.core.security import create_access_token, create_oauth_state, decode_oauth_state
from app.models.base import OAuthProvider
from app.models.user import User
from app.services.auth import (
    AuthError,
    authenticate_user,
    exchange_google_code,
    register_user,
    upsert_oauth_user,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _user_out(user: User) -> UserOut:
    return UserOut(
        id=user.id,
        email=user.email,
        is_verified=user.is_verified,
        karma_score=user.karma_score,
        profile=ProfileOut.model_validate(user.profile) if user.profile else None,
        oauth_accounts=[OAuthAccountOut.model_validate(o) for o in user.oauth_accounts],
    )


def _token_response(user: User) -> TokenOut:
    token = create_access_token(user.id, extra={"email": user.email})
    return TokenOut(access_token=token)


@router.post("/register", response_model=TokenOut)
async def register(
    body: RegisterIn,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> TokenOut:
    try:
        user = await register_user(
            session,
            email=body.email,
            password=body.password,
            full_name=body.full_name,
        )
    except AuthError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _token_response(user)


@router.post("/login", response_model=TokenOut)
async def login(
    body: LoginIn,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> TokenOut:
    try:
        user = await authenticate_user(session, body.email, body.password)
    except AuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    return _token_response(user)


@router.get("/me", response_model=UserOut)
async def me(user: Annotated[User, Depends(get_current_user)]) -> UserOut:
    return _user_out(user)


@router.get("/google/login")
async def google_login() -> RedirectResponse:
    if not settings.google_client_id:
        raise HTTPException(status_code=503, detail="Google OAuth no configurado")
    state = create_oauth_state("google")
    params = urlencode({
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "online",
        "prompt": "select_account",
    })
    return RedirectResponse(f"https://accounts.google.com/o/oauth2/v2/auth?{params}")


@router.get("/google/callback")
async def google_callback(
    session: Annotated[AsyncSession, Depends(get_session)],
    code: str = Query(...),
    state: str = Query(...),
) -> RedirectResponse:
    if not decode_oauth_state(state, "google"):
        raise HTTPException(status_code=400, detail="State inválido")
    try:
        info = await exchange_google_code(code)
        user = await upsert_oauth_user(
            session,
            provider=OAuthProvider.GOOGLE,
            provider_user_id=info["sub"],
            email=info.get("email"),
            display_name=info.get("name"),
            avatar_url=info.get("picture"),
        )
    except Exception as exc:
        msg = quote(str(exc)[:200])
        return RedirectResponse(f"{settings.frontend_url}/auth/callback?error={msg}")

    token = create_access_token(user.id, extra={"email": user.email})
    return RedirectResponse(f"{settings.frontend_url}/auth/callback?token={token}")


