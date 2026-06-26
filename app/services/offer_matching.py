"""Matching semántico CV ↔ ofertas vía embeddings pgvector."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import func, or_, select
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import Select

from app.models.base import Modality, OfferStatus, Seniority
from app.models.offer import Offer
from app.models.profile import Profile
from app.models.source import Source
from app.models.user import User
from app.services.location_filter import location_like_patterns


def distance_to_match_score(distance: float | None) -> float | None:
    """Convierte distancia coseno (0=igual) a porcentaje 0–100."""
    if distance is None:
        return None
    score = (1.0 - float(distance)) * 100.0
    return round(max(0.0, min(100.0, score)), 1)


def cv_embedding_from_user(user: User | None) -> list[float] | None:
    if user is None or user.profile is None:
        return None
    emb = user.profile.cv_embedding
    return list(emb) if emb is not None else None


def base_offers_query() -> Select:
    return (
        select(Offer)
        .join(Source)
        .where(Offer.status == OfferStatus.ACTIVE)
        .options(selectinload(Offer.source))
    )


def apply_offer_filters(
    query: Select,
    *,
    q: str | None = None,
    location: str | None = None,
    modality: list[Modality] | None = None,
    seniority: list[Seniority] | None = None,
    slug_filter: list[str] | None = None,
    salary_min: float | None = None,
    published_within: str | None = None,
    profile: Profile | None = None,
    apply_profile_prefs: bool = False,
) -> Select:
    """Aplica filtros de búsqueda; opcionalmente mezcla preferencias del perfil."""
    if q:
        pattern = f"%{q.lower()}%"
        query = query.where(
            or_(
                func.lower(Offer.title).like(pattern),
                func.lower(Offer.company).like(pattern),
                func.lower(Offer.normalized_title).like(pattern),
                func.lower(Offer.normalized_company).like(pattern),
                func.lower(Offer.description).like(pattern),
            )
        )

    if location:
        patterns = location_like_patterns(location)
        if patterns:
            query = query.where(
                or_(*[func.lower(Offer.location).like(p) for p in patterns])
            )
    elif apply_profile_prefs and profile and profile.preferred_locations:
        loc_patterns: list[str] = []
        for loc in profile.preferred_locations:
            pats = location_like_patterns(loc)
            if pats:
                loc_patterns.extend(pats)
        if loc_patterns:
            query = query.where(
                or_(*[func.lower(Offer.location).like(p) for p in loc_patterns])
            )

    eff_modality = modality
    if not eff_modality and apply_profile_prefs and profile and profile.preferred_modalities:
        eff_modality = profile.preferred_modalities
    if eff_modality:
        query = query.where(Offer.modality.in_(eff_modality))

    eff_seniority = seniority
    if (
        not eff_seniority
        and apply_profile_prefs
        and profile
        and profile.seniority
        and profile.seniority != Seniority.UNKNOWN
    ):
        eff_seniority = [profile.seniority]
    if eff_seniority:
        query = query.where(Offer.seniority.in_(eff_seniority))

    if slug_filter:
        query = query.where(Source.slug.in_(slug_filter))

    eff_salary = salary_min
    if eff_salary is None and apply_profile_prefs and profile and profile.min_salary is not None:
        eff_salary = float(profile.min_salary)
    if eff_salary is not None:
        query = query.where(Offer.salary_min >= eff_salary)

    if published_within:
        now = datetime.now(UTC)
        deltas = {"today": 1, "week": 7, "month": 30}
        since = now - timedelta(days=deltas[published_within])
        query = query.where(Offer.published_at >= since)

    return query


def apply_sort(
    query: Select,
    *,
    sort: str,
    cv_embedding: list[float] | None = None,
) -> tuple[Select, bool]:
    """Ordena resultados. Devuelve (query, usa_matching_cv)."""
    if sort == "salary":
        return query.order_by(
            Offer.salary_max.desc().nullslast(), Offer.published_at.desc()
        ), False

    if sort == "relevance" and cv_embedding is not None:
        query = query.where(Offer.embedding.isnot(None))
        distance = Offer.embedding.cosine_distance(cv_embedding).label("match_distance")
        return (
            query.add_columns(distance).order_by(
                distance, Offer.published_at.desc().nullslast()
            ),
            True,
        )

    return (
        query.order_by(Offer.published_at.desc().nullslast(), Offer.created_at.desc()),
        False,
    )