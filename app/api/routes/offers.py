"""Endpoints de ofertas laborales."""

from __future__ import annotations

import math
import uuid
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_session
from app.api.schemas import CompanyWarningOut, OfferDetail, OfferSummary, PaginatedOffers, SourceOut
from app.services.company_reports import get_company_warning
from app.services.location_filter import location_like_patterns
from app.models.base import Modality, OfferStatus, Seniority
from app.models.offer import Offer
from app.models.source import Source

router = APIRouter(prefix="/offers", tags=["offers"])


def _offer_to_summary(
    offer: Offer,
    *,
    duplicate_count: int = 1,
    company_warning: CompanyWarningOut | None = None,
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
    )


@router.get("", response_model=PaginatedOffers)
async def list_offers(
    session: Annotated[AsyncSession, Depends(get_session)],
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
    query = (
        select(Offer)
        .join(Source)
        .where(Offer.status == OfferStatus.ACTIVE)
        .options(selectinload(Offer.source))
    )

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

    if modality:
        query = query.where(Offer.modality.in_(modality))

    if seniority:
        query = query.where(Offer.seniority.in_(seniority))

    slug_filter = sources or ([source] if source else None)
    if slug_filter:
        query = query.where(Source.slug.in_(slug_filter))

    if salary_min is not None:
        query = query.where(Offer.salary_min >= salary_min)

    if published_within:
        now = datetime.now(UTC)
        deltas = {"today": 1, "week": 7, "month": 30}
        since = now - timedelta(days=deltas[published_within])
        query = query.where(Offer.published_at >= since)

    if sort == "salary":
        query = query.order_by(Offer.salary_max.desc().nullslast(), Offer.published_at.desc())
    elif sort == "relevance" and q:
        query = query.order_by(Offer.published_at.desc())
    else:
        query = query.order_by(Offer.published_at.desc().nullslast(), Offer.created_at.desc())

    count_result = await session.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar_one()

    offset = (page - 1) * page_size
    result = await session.execute(query.offset(offset).limit(page_size))
    offers = result.scalars().all()

    # Contar duplicados por fingerprint
    fingerprints = [o.fingerprint for o in offers]
    dup_map: dict[str, int] = {}
    if fingerprints:
        dup_result = await session.execute(
            select(Offer.fingerprint, func.count())
            .where(Offer.fingerprint.in_(fingerprints), Offer.status == OfferStatus.ACTIVE)
            .group_by(Offer.fingerprint)
        )
        dup_map = dict(dup_result.all())

    items = [_offer_to_summary(o, duplicate_count=dup_map.get(o.fingerprint, 1)) for o in offers]
    pages = max(1, math.ceil(total / page_size)) if total else 1

    return PaginatedOffers(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
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

    similar: list[OfferSummary] = []
    if offer.embedding is not None:
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
            .limit(4)
        )
        similar = [_offer_to_summary(o) for o in similar_result.scalars().all()]

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