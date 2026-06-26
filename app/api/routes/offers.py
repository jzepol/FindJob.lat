"""Endpoints de ofertas laborales."""

from __future__ import annotations

import math
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, get_current_user_optional, get_session
from app.api.schemas import CompanyWarningOut, OfferDetail, OfferSummary, PaginatedOffers, SourceOut
from app.models.base import Modality, OfferStatus, Seniority
from app.models.offer import Offer
from app.models.source import Source
from app.models.user import User
from app.services.company_reports import get_company_warning
from app.services.offer_matching import (
    apply_offer_filters,
    apply_sort,
    base_offers_query,
    cv_embedding_from_user,
    distance_to_match_score,
)

router = APIRouter(prefix="/offers", tags=["offers"])


def _offer_to_summary(
    offer: Offer,
    *,
    duplicate_count: int = 1,
    company_warning: CompanyWarningOut | None = None,
    match_score: float | None = None,
) -> OfferSummary:
    return OfferSummary(
        id=offer.id,
        title=offer.title,
        company=offer.company,
        location=offer.location,
        modality=offer.modality,
        job_type=offer.job_type,
        seniority=offer.seniority,
        status=offer.status,
        salary_min=offer.salary_min,
        salary_max=offer.salary_max,
        salary_currency=offer.salary_currency,
        url=offer.url,
        published_at=offer.published_at,
        source=SourceOut.model_validate(offer.source),
        created_at=offer.created_at,
        updated_at=offer.updated_at,
        duplicate_count=duplicate_count,
        company_warning=company_warning,
        match_score=match_score,
    )


async def _duplicate_counts(
    session: AsyncSession,
    offers: list[Offer],
) -> dict[str, int]:
    fingerprints = [o.fingerprint for o in offers]
    if not fingerprints:
        return {}
    dup_result = await session.execute(
        select(Offer.fingerprint, func.count())
        .where(Offer.fingerprint.in_(fingerprints), Offer.status == OfferStatus.ACTIVE)
        .group_by(Offer.fingerprint)
    )
    return dict(dup_result.all())


async def _paginate_offers(
    session: AsyncSession,
    *,
    q: str | None,
    location: str | None,
    modality: list[Modality] | None,
    seniority: list[Seniority] | None,
    slug_filter: list[str] | None,
    salary_min: float | None,
    published_within: str | None,
    sort: str,
    page: int,
    page_size: int,
    user: User | None = None,
    apply_profile_prefs: bool = False,
) -> PaginatedOffers:
    query = base_offers_query()
    profile = user.profile if user else None

    query = apply_offer_filters(
        query,
        q=q,
        location=location,
        modality=modality,
        seniority=seniority,
        slug_filter=slug_filter,
        salary_min=salary_min,
        published_within=published_within,
        profile=profile,
        apply_profile_prefs=apply_profile_prefs,
    )

    count_result = await session.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar_one()

    cv_emb = cv_embedding_from_user(user)
    query, cv_matching = apply_sort(query, sort=sort, cv_embedding=cv_emb)

    offset = (page - 1) * page_size
    result = await session.execute(query.offset(offset).limit(page_size))

    offers: list[Offer] = []
    scores: list[float | None] = []
    if cv_matching:
        for row in result.all():
            offers.append(row[0])
            scores.append(distance_to_match_score(row[1]))
    else:
        offers = list(result.scalars().all())
        scores = [None] * len(offers)

    dup_map = await _duplicate_counts(session, offers)
    items = [
        _offer_to_summary(
            o,
            duplicate_count=dup_map.get(o.fingerprint, 1),
            match_score=score,
        )
        for o, score in zip(offers, scores, strict=True)
    ]
    pages = max(1, math.ceil(total / page_size)) if total else 1

    return PaginatedOffers(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
        matching_mode="cv" if cv_matching else None,
    )


@router.get("", response_model=PaginatedOffers)
async def list_offers(
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[User | None, Depends(get_current_user_optional)],
    q: str | None = None,
    location: str | None = None,
    modality: list[Modality] | None = Query(None),
    seniority: list[Seniority] | None = Query(None),
    source: str | None = None,
    sources: list[str] | None = Query(None, description="Filtrar por uno o más portales"),
    salary_min: float | None = None,
    published_within: str | None = Query(None, pattern="^(today|week|month)$"),
    sort: str = Query("published_at", pattern="^(relevance|published_at|salary)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> PaginatedOffers:
    slug_filter = sources or ([source] if source else None)
    return await _paginate_offers(
        session,
        q=q,
        location=location,
        modality=modality,
        seniority=seniority,
        slug_filter=slug_filter,
        salary_min=salary_min,
        published_within=published_within,
        sort=sort,
        page=page,
        page_size=page_size,
        user=user,
    )


@router.get("/for-me", response_model=PaginatedOffers)
async def offers_for_me(
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> PaginatedOffers:
    """Ofertas recomendadas según CV y preferencias del perfil."""
    if cv_embedding_from_user(user) is None:
        raise HTTPException(
            status_code=400,
            detail="Subí tu CV en el perfil para activar recomendaciones personalizadas.",
        )

    return await _paginate_offers(
        session,
        q=None,
        location=None,
        modality=None,
        seniority=None,
        slug_filter=None,
        salary_min=None,
        published_within=None,
        sort="relevance",
        page=page,
        page_size=page_size,
        user=user,
        apply_profile_prefs=True,
    )


@router.get("/featured", response_model=list[OfferSummary])
async def featured_offers(
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: int = Query(6, ge=1, le=20),
) -> list[OfferSummary]:
    result = await session.execute(
        select(Offer)
        .join(Source)
        .where(Offer.status == OfferStatus.ACTIVE, Offer.description.isnot(None))
        .options(selectinload(Offer.source))
        .order_by(Offer.published_at.desc().nullslast())
        .limit(limit)
    )
    return [_offer_to_summary(o) for o in result.scalars().all()]


@router.get("/{offer_id}", response_model=OfferDetail)
async def get_offer(
    offer_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[User | None, Depends(get_current_user_optional)],
) -> OfferDetail:
    result = await session.execute(
        select(Offer)
        .where(Offer.id == offer_id)
        .options(selectinload(Offer.source))
    )
    offer = result.scalar_one_or_none()
    if offer is None:
        raise HTTPException(status_code=404, detail="Oferta no encontrada")

    dup_result = await session.execute(
        select(Offer)
        .join(Source)
        .where(
            Offer.fingerprint == offer.fingerprint,
            Offer.id != offer.id,
            Offer.status == OfferStatus.ACTIVE,
        )
        .options(selectinload(Offer.source))
        .limit(10)
    )
    duplicates = [_offer_to_summary(o) for o in dup_result.scalars().all()]

    cv_emb = cv_embedding_from_user(user)
    match_score: float | None = None
    if cv_emb is not None and offer.embedding is not None:
        dist_result = await session.execute(
            select(Offer.embedding.cosine_distance(cv_emb)).where(Offer.id == offer_id)
        )
        match_score = distance_to_match_score(dist_result.scalar_one())

    warning_data = await get_company_warning(
        session,
        normalized_company=offer.normalized_company,
        company_name=offer.company,
    )
    warning = CompanyWarningOut(**warning_data) if warning_data else None

    summary = _offer_to_summary(
        offer,
        duplicate_count=1 + len(duplicates),
        company_warning=warning,
        match_score=match_score,
    )
    detail = OfferDetail(
        **summary.model_dump(),
        normalized_title=offer.normalized_title,
        normalized_company=offer.normalized_company,
        description=offer.description,
        external_id=offer.external_id,
        has_embedding=offer.embedding is not None,
        duplicates=duplicates,
    )
    detail.duplicate_count = 1 + len(duplicates)
    return detail


@router.get("/{offer_id}/similar", response_model=list[OfferSummary])
async def similar_offers(
    offer_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: int = Query(4, ge=1, le=12),
) -> list[OfferSummary]:
    result = await session.execute(select(Offer).where(Offer.id == offer_id))
    offer = result.scalar_one_or_none()
    if offer is None:
        raise HTTPException(status_code=404, detail="Oferta no encontrada")

    if offer.embedding is None:
        fallback = await session.execute(
            select(Offer)
            .join(Source)
            .where(
                Offer.id != offer.id,
                Offer.status == OfferStatus.ACTIVE,
                Offer.seniority == offer.seniority,
            )
            .options(selectinload(Offer.source))
            .order_by(Offer.published_at.desc().nullslast())
            .limit(limit)
        )
        return [_offer_to_summary(o) for o in fallback.scalars().all()]

    similar_result = await session.execute(
        select(Offer)
        .join(Source)
        .where(
            Offer.id != offer.id,
            Offer.status == OfferStatus.ACTIVE,
            Offer.embedding.isnot(None),
        )
        .options(selectinload(Offer.source))
        .order_by(Offer.embedding.cosine_distance(offer.embedding))
        .limit(limit)
    )
    return [_offer_to_summary(o) for o in similar_result.scalars().all()]