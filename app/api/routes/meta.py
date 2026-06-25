"""Endpoints de metadatos: sources, enums, stats, salarios."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.api.schemas import EnumsOut, SalaryRoleOut, SourceOut, StatsOut
from app.models.base import JobType, Modality, OfferStatus, Seniority
from app.models.offer import Offer
from app.models.source import Source

router = APIRouter(tags=["meta"])


@router.get("/sources", response_model=list[SourceOut])
async def list_sources(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[SourceOut]:
    result = await session.execute(
        select(Source).where(Source.is_active.is_(True)).order_by(Source.name)
    )
    return [SourceOut.model_validate(s) for s in result.scalars().all()]


@router.get("/enums", response_model=EnumsOut)
async def list_enums() -> EnumsOut:
    return EnumsOut(
        modality=[m.value for m in Modality],
        job_type=[j.value for j in JobType],
        seniority=[s.value for s in Seniority],
        offer_status=[o.value for o in OfferStatus],
    )


@router.get("/stats", response_model=StatsOut)
async def get_stats(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> StatsOut:
    active = await session.execute(
        select(func.count()).select_from(Offer).where(Offer.status == OfferStatus.ACTIVE)
    )
    companies = await session.execute(
        select(func.count(func.distinct(Offer.company))).where(Offer.status == OfferStatus.ACTIVE)
    )
    sources = await session.execute(
        select(func.count()).select_from(Source).where(Source.is_active.is_(True))
    )
    with_salary = await session.execute(
        select(func.count())
        .select_from(Offer)
        .where(Offer.status == OfferStatus.ACTIVE, Offer.salary_min.isnot(None))
    )
    return StatsOut(
        active_offers=active.scalar_one(),
        companies=companies.scalar_one(),
        sources=sources.scalar_one(),
        with_salary=with_salary.scalar_one(),
    )


@router.get("/salaries", response_model=list[SalaryRoleOut])
async def salary_overview(
    session: Annotated[AsyncSession, Depends(get_session)],
    seniority: Seniority | None = None,
    location: str | None = None,
    limit: int = Query(12, ge=1, le=50),
) -> list[SalaryRoleOut]:
    query = (
        select(
            Offer.normalized_title,
            Offer.seniority,
            func.count().label("count"),
            func.min(Offer.salary_min).label("salary_min"),
            func.max(Offer.salary_max).label("salary_max"),
            func.avg(
                func.coalesce(
                    (Offer.salary_min + Offer.salary_max) / 2,
                    Offer.salary_min,
                    Offer.salary_max,
                )
            ).label("salary_avg"),
            Offer.salary_currency,
        )
        .where(
            Offer.status == OfferStatus.ACTIVE,
            Offer.salary_min.isnot(None),
            Offer.normalized_title.isnot(None),
        )
        .group_by(Offer.normalized_title, Offer.seniority, Offer.salary_currency)
        .order_by(func.count().desc())
        .limit(limit)
    )

    if seniority:
        query = query.where(Offer.seniority == seniority)

    if location:
        query = query.where(func.lower(Offer.location).like(f"%{location.lower()}%"))

    result = await session.execute(query)
    rows = result.all()

    return [
        SalaryRoleOut(
            role=(row.normalized_title or "Sin título").title(),
            seniority=row.seniority,
            count=row.count,
            salary_min=row.salary_min,
            salary_max=row.salary_max,
            salary_avg=row.salary_avg,
            currency=row.salary_currency,
        )
        for row in rows
    ]