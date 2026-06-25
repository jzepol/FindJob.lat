"""Lógica de reportes de empresas y advertencias."""

from __future__ import annotations

import uuid

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.base import CompanyReportStatus, CompanyReportType
from app.models.company_report import CompanyReport
from app.services.normalizer import normalize_text

logger = structlog.get_logger(__name__)


def normalize_company(name: str) -> str:
    return normalize_text(name)[:255] or "unknown"


async def get_company_warning(
    session: AsyncSession,
    *,
    normalized_company: str | None,
    company_name: str | None = None,
) -> dict | None:
    """Retorna advertencia si la empresa supera el umbral de reportes verificados."""
    key = normalized_company or (normalize_company(company_name) if company_name else None)
    if not key or key == "unknown":
        return None

    result = await session.execute(
        select(
            CompanyReport.report_type,
            func.count().label("cnt"),
        )
        .where(
            CompanyReport.normalized_company == key,
            CompanyReport.status == CompanyReportStatus.VERIFIED,
        )
        .group_by(CompanyReport.report_type)
    )
    rows = result.all()
    if not rows:
        return None

    total = sum(r.cnt for r in rows)
    if total < settings.company_warning_threshold:
        return None

    top_type = max(rows, key=lambda r: r.cnt)
    return {
        "company": company_name or key,
        "normalized_company": key,
        "verified_reports": total,
        "primary_issue": top_type.report_type.value,
        "breakdown": {r.report_type.value: r.cnt for r in rows},
        "severity": "high" if total >= settings.company_warning_threshold * 2 else "medium",
        "message": _warning_message(top_type.report_type, total),
    }


def _warning_message(report_type: CompanyReportType, count: int) -> str:
    messages = {
        CompanyReportType.GHOST_JOB: (
            f"{count} reportes verificados indican que este puesto podría no existir "
            "o estar publicado solo para captar CVs."
        ),
        CompanyReportType.HIGH_TURNOVER: (
            f"{count} reportes verificados señalan alta rotación en esta empresa."
        ),
        CompanyReportType.MISLEADING_SALARY: (
            f"{count} reportes verificados indican salarios engañosos o no informados."
        ),
        CompanyReportType.ATS_BLACK_HOLE: (
            f"{count} reportes verificados: muchos postulantes, pocas respuestas. "
            "Revisá el proceso de selección, no solo tu perfil."
        ),
        CompanyReportType.OTHER: (
            f"{count} reportes verificados de la comunidad sobre esta empresa."
        ),
    }
    return messages.get(report_type, messages[CompanyReportType.OTHER])


async def try_crowd_verify(
    session: AsyncSession,
    *,
    normalized_company: str,
    report_type: CompanyReportType,
) -> int:
    """Auto-verifica si >= N usuarios distintos reportaron lo mismo (crowd consensus)."""
    result = await session.execute(
        select(CompanyReport)
        .where(
            CompanyReport.normalized_company == normalized_company,
            CompanyReport.report_type == report_type,
            CompanyReport.status == CompanyReportStatus.PENDING,
        )
    )
    pending = list(result.scalars().all())
    unique_users = {r.user_id for r in pending}

    if len(unique_users) < settings.company_crowd_verify_threshold:
        return 0

    verified = 0
    for report in pending:
        report.status = CompanyReportStatus.VERIFIED
        verified += 1

    await session.flush()
    logger.info(
        "company_reports_crowd_verified",
        company=normalized_company,
        report_type=report_type.value,
        count=verified,
    )
    return verified


async def user_already_reported(
    session: AsyncSession,
    user_id: uuid.UUID,
    normalized_company: str,
) -> bool:
    result = await session.execute(
        select(func.count())
        .select_from(CompanyReport)
        .where(
            CompanyReport.user_id == user_id,
            CompanyReport.normalized_company == normalized_company,
            CompanyReport.status != CompanyReportStatus.REJECTED,
        )
    )
    return (result.scalar_one() or 0) > 0