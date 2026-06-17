"""Persistencia de ofertas scrapeadas con deduplicación."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Modality, OfferStatus
from app.models.offer import Offer
from app.models.source import ScrapeRun, ScrapeRunStatus, Source
from app.scrapers.registry import scraper_class_path
from app.scrapers.schemas import IngestResult, RawOffer
from app.core.config import settings
from app.services.normalizer import (
    make_fingerprint,
    normalize_text,
    parse_job_type,
    parse_modality,
    parse_published_at,
    parse_salary,
    parse_seniority,
)

logger = structlog.get_logger(__name__)

def _computrabajo_source_defaults() -> dict[str, Any]:
    from app.core.config import settings

    country_names = {
        "ar": "Argentina",
        "co": "Colombia",
        "mx": "México",
        "pe": "Perú",
        "cl": "Chile",
    }
    country = settings.computrabajo_country
    label = country_names.get(country, country.upper())
    return {
        "name": f"Computrabajo {label}",
        "base_url": settings.computrabajo_base_url,
    }


from collections.abc import Callable

SOURCE_DEFAULTS: dict[str, dict[str, Any] | Callable[[], dict[str, Any]]] = {
    "computrabajo": _computrabajo_source_defaults,
    "remoteok": lambda: {
        "name": "Remote OK",
        "base_url": "https://remoteok.com",
    },
    "bumeran": lambda: {
        "name": "Bumeran Argentina",
        "base_url": "https://www.bumeran.com.ar",
    },
}


async def ensure_source(session: AsyncSession, slug: str) -> Source:
    """Obtiene o crea la fila Source para un portal."""
    result = await session.execute(select(Source).where(Source.slug == slug))
    source = result.scalar_one_or_none()

    defaults_fn = SOURCE_DEFAULTS.get(slug)
    if defaults_fn is None:
        raise ValueError(f"No hay defaults configurados para la fuente {slug!r}")

    defaults = defaults_fn() if callable(defaults_fn) else defaults_fn

    if source is not None:
        # Sincronizar país/base_url si cambió la configuración
        if source.base_url != defaults["base_url"] or source.name != defaults["name"]:
            source.name = defaults["name"]
            source.base_url = defaults["base_url"]
            await session.flush()
            logger.info("source_updated", slug=slug, base_url=defaults["base_url"])
        return source

    source = Source(
        name=defaults["name"],
        slug=slug,
        base_url=defaults["base_url"],
        scraper_class=scraper_class_path(slug),
        is_active=True,
    )
    session.add(source)
    await session.flush()
    logger.info("source_created", slug=slug, source_id=str(source.id))
    return source


def raw_to_offer_fields(raw: RawOffer, *, source: Source) -> dict[str, Any]:
    """Mapea RawOffer → campos del modelo Offer."""
    detail = raw.raw_data.get("detail") or {}
    header_tags: list[str] = detail.get("header_tags") or []
    # meta_items incluye ofertas similares — solo usamos educación/experiencia
    meta_items: list[str] = detail.get("meta_items") or []
    experience_meta = [
        m for m in meta_items
        if any(k in m.lower() for k in ("experiencia", "educación", "educacion", "estudios"))
    ]
    job_type_context = " ".join([raw.title, raw.description or "", *header_tags])

    modality_icons = raw.raw_data.get("modality_icons") or raw.raw_data.get("modalityIcons")
    tags: list[str] = raw.raw_data.get("tags") or []
    default_modality = Modality.REMOTE if source.slug == "remoteok" else Modality.ON_SITE

    modality = parse_modality(
        raw.modality_raw,
        raw.title,
        raw.location,
        raw.description,
        *header_tags,
        *tags,
        icons=modality_icons,
        default=default_modality,
    )

    salary_country = "us" if source.slug == "remoteok" else settings.computrabajo_country
    parsed_salary = parse_salary(raw.salary_raw, country=salary_country)

    if source.slug == "remoteok" and parsed_salary.salary_min is None:
        api_min = raw.raw_data.get("salary_min")
        api_max = raw.raw_data.get("salary_max")
        if api_min and int(api_min) > 0:
            from decimal import Decimal

            parsed_salary.salary_min = Decimal(str(api_min))
            if api_max and int(api_max) > int(api_min):
                parsed_salary.salary_max = Decimal(str(api_max))
            parsed_salary.currency = "USD"

    return {
        "external_id": raw.external_id,
        "fingerprint": make_fingerprint(
            title=raw.title,
            company=raw.company,
            location=raw.location,
            source_slug=source.slug,
            external_id=raw.external_id,
        ),
        "title": raw.title[:500],
        "normalized_title": normalize_text(raw.title)[:500] or None,
        "company": (raw.company or "—")[:255],
        "normalized_company": normalize_text(raw.company)[:255] or None,
        "description": raw.description,
        "location": (raw.location or None),
        "modality": modality,
        "job_type": parse_job_type(job_type_context, *tags),
        "seniority": parse_seniority(
            raw.title,
            " ".join([raw.description or "", *experience_meta]),
        ),
        "status": OfferStatus.ACTIVE,
        "salary_min": parsed_salary.salary_min,
        "salary_max": parsed_salary.salary_max,
        "salary_currency": parsed_salary.currency,
        "url": raw.url[:1024],
        "published_at": parse_published_at(raw.posted_at_raw),
        "raw_data": raw.raw_data,
    }


async def ingest_offers(
    session: AsyncSession,
    *,
    source: Source,
    raw_offers: list[RawOffer],
) -> IngestResult:
    """Upsert de ofertas por (source_id, external_id)."""
    result = IngestResult(found=len(raw_offers))

    for raw in raw_offers:
        fields = raw_to_offer_fields(raw, source=source)

        existing = await session.execute(
            select(Offer).where(
                Offer.source_id == source.id,
                Offer.external_id == fields["external_id"],
            )
        )
        offer = existing.scalar_one_or_none()

        if offer is None:
            offer = Offer(source_id=source.id, **fields)
            session.add(offer)
            result.new += 1
        else:
            for key, value in fields.items():
                setattr(offer, key, value)
            result.updated += 1

    await session.flush()
    logger.info(
        "ingest_completed",
        source=source.slug,
        found=result.found,
        new=result.new,
        updated=result.updated,
    )
    return result


async def create_scrape_run(session: AsyncSession, source_id: uuid.UUID) -> ScrapeRun:
    """Crea un ScrapeRun en estado RUNNING."""
    run = ScrapeRun(
        source_id=source_id,
        status=ScrapeRunStatus.RUNNING,
        started_at=datetime.now(UTC),
    )
    session.add(run)
    await session.flush()
    return run


async def finish_scrape_run(
    session: AsyncSession,
    run: ScrapeRun,
    *,
    result: IngestResult,
    error: str | None = None,
) -> None:
    """Cierra un ScrapeRun con métricas o error."""
    run.finished_at = datetime.now(UTC)
    run.offers_found = result.found
    run.offers_new = result.new
    run.offers_updated = result.updated

    if error:
        run.status = ScrapeRunStatus.FAILED
        run.error_message = error
    else:
        run.status = ScrapeRunStatus.COMPLETED