"""Perfil del usuario y karma."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_session
from app.api.schemas import KarmaOut, ProfileOut, ProfileUpdateIn, UserOut
from app.models.base import KarmaEventType
from app.models.profile import Profile
from app.models.user import User
from app.services.karma import award_karma, karma_progress, sync_profile_karma

router = APIRouter(prefix="/me", tags=["users"])


@router.get("", response_model=UserOut)
async def get_me(user: Annotated[User, Depends(get_current_user)]) -> UserOut:
    from app.api.routes.auth import _user_out

    return _user_out(user)


@router.patch("/profile", response_model=ProfileOut)
async def update_profile(
    body: ProfileUpdateIn,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
) -> ProfileOut:
    profile = user.profile
    if profile is None:
        profile = Profile(user_id=user.id)
        session.add(profile)
        user.profile = profile

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)

    await sync_profile_karma(session, user, profile)
    await session.flush()
    return ProfileOut.model_validate(profile)


@router.get("/karma", response_model=KarmaOut)
async def get_karma(user: Annotated[User, Depends(get_current_user)]) -> KarmaOut:
    return KarmaOut(**karma_progress(user))


@router.post("/activity/search")
async def record_search(
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
) -> dict:
    """Registra primera búsqueda para karma."""
    gained = await award_karma(session, user, KarmaEventType.FIRST_SEARCH)
    return {"karma_gained": gained, "karma_score": user.karma_score}