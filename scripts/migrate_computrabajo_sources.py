#!/usr/bin/env python3
"""Reasigna ofertas del slug legacy 'computrabajo' a computrabajo-{país}."""

from __future__ import annotations

import asyncio
import uuid

import structlog
from sqlalchemy import select

from app.core.database import async_session_factory
from app.models.offer import Offer
from app.models.source import Source
from app.services.offer_ingest import ensure_source
from app.services.source_defaults import computrabajo_slug

structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer(),
    ],
)
logger = structlog.get_logger(__name__)


def infer_slug(location: str | None) -> str:
    loc = (location or "").lower()
    if any(
        x in loc
        for x in (
            "r.metropolitana",
            "santiago -",
            "santiago centro",
            ", lima",
            "valparaíso",
            "valparaiso",
        )
    ):
        if "lima" in loc or "perú" in loc or "peru" in loc:
            return computrabajo_slug("pe")
        return computrabajo_slug("cl")
    if any(x in loc for x in ("bogota", "bogotá", "medellin", "medellín", "colombia")):
        return computrabajo_slug("co")
    if any(x in loc for x in ("cdmx", "ciudad de mexico", "guadalajara", "monterrey", "méxico")):
        return computrabajo_slug("mx")
    if any(x in loc for x in ("lima", "perú", "peru", "arequipa")):
        return computrabajo_slug("pe")
    if any(
        x in loc
        for x in (
            "buenos aires",
            "gba",
            "caba",
            "córdoba",
            "cordoba",
            "rosario",
            "mendoza",
            "la plata",
        )
    ):
        return computrabajo_slug("ar")
    return computrabajo_slug("ar")


async def run() -> None:
    async with async_session_factory() as session:
        legacy = await session.execute(select(Source).where(Source.slug == "computrabajo"))
        legacy_source = legacy.scalar_one_or_none()
        if legacy_source is None:
            print("No hay fuente legacy 'computrabajo'. Nada que migrar.")
            return

        offers = (
            await session.execute(select(Offer).where(Offer.source_id == legacy_source.id))
        ).scalars().all()

        moved = 0
        cache: dict[str, uuid.UUID] = {}
        for offer in offers:
            slug = infer_slug(offer.location)
            if slug not in cache:
                src = await ensure_source(session, slug)
                cache[slug] = src.id
            offer.source_id = cache[slug]
            moved += 1

        legacy_source.is_active = False
        await session.commit()
        logger.info("migrate_done", offers=moved, targets=sorted(cache.keys()))
        print(f"\n✓ {moved} ofertas reasignadas → {', '.join(sorted(cache.keys()))}\n")


if __name__ == "__main__":
    asyncio.run(run())