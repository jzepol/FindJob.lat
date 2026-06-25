"""Reportes de empresas con gate de karma."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_session
from app.api.schemas import CompanyReportIn, CompanyReportOut, CompanyWarningOut
from app.models.company_report import CompanyReport
from app.models.offer import Offer
from app.models.user import User
from app.services.company_reports import (
    get_company_warning,
    normalize_company,
    try_crowd_verify,
    user_already_reported,
)
from app.core.config import settings
from app.services.karma import can_report

router = APIRouter(prefix="/company-reports", tags=["company-reports"])


@router.post("", response_model=CompanyReportOut, status_code=201)
async def create_report(
    body: CompanyReportIn,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
) -> CompanyReportOut:
    if not can_report(user):
        raise HTTPException(
            status_code=403,
            detail={
                "message": "Karma insuficiente para reportar",
                "karma_score": user.karma_score,
                "min_required": settings.karma_min_to_report,
                "hint": "Completá tu perfil, subí tu CV y hacé búsquedas para ganar karma",
            },
        )

    company_name = body.company_name.strip()
    normalized = normalize_company(company_name)
    offer_id = body.offer_id

    if offer_id:
        result = await session.execute(select(Offer).where(Offer.id == offer_id))
        offer = result.scalar_one_or_none()
        if offer:
            company_name = offer.company
            normalized = offer.normalized_company or normalize_company(offer.company)

    if await user_already_reported(session, user.id, normalized):
        raise HTTPException(status_code=409, detail="Ya reportaste esta empresa")

    report = CompanyReport(
        user_id=user.id,
        offer_id=offer_id,
        company_name=company_name,
        normalized_company=normalized,
        report_type=body.report_type,
        description=body.description,
    )
    session.add(report)
    await session.flush()

    await try_crowd_verify(session, normalized_company=normalized, report_type=body.report_type)

    return CompanyReportOut.model_validate(report)


@router.get("/warnings/{normalized_company}", response_model=CompanyWarningOut | None)
async def company_warning(
    normalized_company: str,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> CompanyWarningOut | None:
    warning = await get_company_warning(session, normalized_company=normalized_company)
    return CompanyWarningOut(**warning) if warning else None