"""Sistema de karma / reputación de usuarios."""

from __future__ import annotations

import uuid

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.base import KarmaEventType
from app.models.karma_event import KarmaEvent
from app.models.profile import Profile
from app.models.user import User

logger = structlog.get_logger(__name__)

KARMA_POINTS: dict[KarmaEventType, int] = {
    KarmaEventType.OAUTH_LINKED: 15,
    KarmaEventType.PROFILE_COMPLETE: 20,
    KarmaEventType.CV_UPLOADED: 25,
    KarmaEventType.FIRST_SEARCH: 10,
    KarmaEventType.EMAIL_VERIFIED: 15,
}


async def award_karma(
    session: AsyncSession,
    user: User,
    event_type: KarmaEventType,
) -> int:
    """Otorga karma si el evento no fue registrado antes. Retorna puntos ganados."""
    existing = await session.execute(
        select(KarmaEvent).where(
            KarmaEvent.user_id == user.id,
            KarmaEvent.event_type == event_type,
        )
    )
    if existing.scalar_one_or_none() is not None:
        return 0

    points = KARMA_POINTS[event_type]
    session.add(KarmaEvent(user_id=user.id, event_type=event_type, points=points))
    user.karma_score += points
    await session.flush()
    logger.info(
        "karma_awarded",
        user_id=str(user.id),
        karma_event=event_type.value,
        points=points,
    )
    return points


async def sync_profile_karma(session: AsyncSession, user: User, profile: Profile) -> None:
    """Recalcula karma derivado del perfil."""
    if profile.full_name and profile.headline:
        await award_karma(session, user, KarmaEventType.PROFILE_COMPLETE)
    if profile.cv_text and len(profile.cv_text.strip()) > 50:
        await award_karma(session, user, KarmaEventType.CV_UPLOADED)


def can_report(user: User) -> bool:
    return user.karma_score >= settings.karma_min_to_report


def karma_progress(user: User) -> dict:
    missing = settings.karma_min_to_report - user.karma_score
    return {
        "score": user.karma_score,
        "min_to_report": settings.karma_min_to_report,
        "can_report": can_report(user),
        "points_needed": max(0, missing),
        "events": {k.value: v for k, v in KARMA_POINTS.items()},
    }