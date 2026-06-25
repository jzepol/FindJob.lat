"""Perfil del usuario y karma."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_session
from app.api.schemas import CvUploadOut, KarmaOut, ProfileOut, ProfileUpdateIn, UserOut
from app.models.base import KarmaEventType
from app.models.profile import Profile
from app.models.user import User
from app.services.cv_intelligence import process_cv_upload
from app.services.embeddings import EmbeddingError, embed_cv_text
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

    payload = body.model_dump(exclude_unset=True)
    for field, value in payload.items():
        setattr(profile, field, value)

    if "cv_text" in payload and profile.cv_text and len(profile.cv_text.strip()) > 50:
        try:
            profile.cv_embedding = await embed_cv_text(
                profile.cv_text,
                headline=profile.headline,
                skills=profile.skills,
            )
        except EmbeddingError:
            pass

    await sync_profile_karma(session, user, profile)
    await session.flush()
    return ProfileOut.model_validate(profile)


@router.post("/profile/cv", response_model=CvUploadOut)
async def upload_cv(
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
    file: UploadFile = File(...),
) -> CvUploadOut:
    """Sube CV → Gemini lo lee, extrae datos, genera embedding y otorga karma."""
    profile = user.profile
    if profile is None:
        profile = Profile(user_id=user.id)
        session.add(profile)
        user.profile = profile

    karma_before = user.karma_score
    parsed = await process_cv_upload(file, profile)
    await sync_profile_karma(session, user, profile)
    await session.flush()

    return CvUploadOut(
        cv_text=parsed.cv_text,
        chars=len(parsed.cv_text),
        filename=file.filename or "cv",
        karma_gained=user.karma_score - karma_before,
        karma_score=user.karma_score,
        parsed_by=parsed.parsed_by,
        embedding_ready=parsed.embedding_ready,
        summary=parsed.summary,
        skills_extracted=parsed.skills,
        headline_extracted=parsed.headline,
        full_name_extracted=parsed.full_name,
    )


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