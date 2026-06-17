#!/usr/bin/env python3
"""Script unificado para scrapear cualquier fuente registrada.

Uso:
    python scripts/scrape.py --source remoteok -k python
    python scripts/scrape.py --source bumeran -k "desarrollador python"
    python scripts/scrape.py --source computrabajo -k "desarrollador python" -l "buenos aires"
"""

from __future__ import annotations

import argparse
import asyncio
import sys

import structlog

from app.core.config import settings
from app.core.database import async_session_factory
from app.scrapers.registry import get_scraper, list_scrapers
from app.scrapers.schemas import IngestResult, ScrapeParams
from app.services.embeddings import embed_scraped_batch
from app.services.offer_ingest import (
    create_scrape_run,
    ensure_source,
    finish_scrape_run,
    ingest_offers,
)

structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer(),
    ],
)
logger = structlog.get_logger(__name__)


async def run(
    source: str,
    keywords: str,
    location: str,
    *,
    fetch_details: bool,
    max_results: int | None,
    embed: bool,
) -> int:
    scraper = get_scraper(source)
    params = ScrapeParams(
        keywords=keywords,
        location=location,
        fetch_details=fetch_details,
        max_results=max_results,
    )

    logger.info(
        "scrape_start",
        source=source,
        keywords=keywords,
        location=location or "(vacío)",
        fetch_details=fetch_details,
    )

    raw_offers = await scraper.run(params)
    if not raw_offers:
        logger.warning("no_offers_found")
        return 1

    with_description = sum(1 for o in raw_offers if o.description)
    logger.info("scrape_parsed", total=len(raw_offers), with_description=with_description)

    result = IngestResult()
    async with async_session_factory() as session:
        db_source = await ensure_source(session, scraper.slug)
        scrape_run = await create_scrape_run(session, db_source.id)

        try:
            result = await ingest_offers(session, source=db_source, raw_offers=raw_offers)
            if embed:
                external_ids = [o.external_id for o in raw_offers]
                result.embedded = await embed_scraped_batch(
                    session,
                    source_id=db_source.id,
                    external_ids=external_ids,
                )
            await finish_scrape_run(session, scrape_run, result=result)
            await session.commit()
        except Exception as exc:
            await finish_scrape_run(
                session,
                scrape_run,
                result=IngestResult(found=len(raw_offers)),
                error=str(exc),
            )
            await session.commit()
            raise

    logger.info(
        "scrape_done",
        found=result.found,
        new=result.new,
        updated=result.updated,
        embedded=result.embedded,
    )
    embed_msg = f", {result.embedded} embeddeadas" if embed else ""
    print(
        f"\n✓ [{source}] {result.found} ofertas — "
        f"{result.new} nuevas, {result.updated} actualizadas"
        f"{embed_msg} "
        f"({with_description} con descripción)\n"
    )
    return 0


def main() -> None:
    sources = ", ".join(list_scrapers())
    parser = argparse.ArgumentParser(description="Scrapear ofertas y guardar en PostgreSQL")
    parser.add_argument("--source", "-s", required=True, choices=list_scrapers(), help=sources)
    parser.add_argument("--keywords", "-k", required=True, help='Ej: "python" o "desarrollador python"')
    parser.add_argument("--location", "-l", default="", help='Ej: "buenos aires" (opcional)')
    parser.add_argument("--no-details", action="store_true", help="Solo listado (portales con detalle)")
    parser.add_argument("--max-results", type=int, default=None, help="Máximo de ofertas")
    parser.add_argument(
        "--no-embeddings",
        action="store_true",
        help="No generar embeddings después del scrape",
    )
    args = parser.parse_args()

    embed = settings.embed_after_scrape and not args.no_embeddings

    try:
        code = asyncio.run(
            run(
                args.source,
                args.keywords,
                args.location,
                fetch_details=not args.no_details,
                max_results=args.max_results,
                embed=embed,
            )
        )
    except Exception as exc:
        logger.exception("scrape_failed", error=str(exc))
        print(f"\n✗ Error: {exc}\n", file=sys.stderr)
        code = 1

    sys.exit(code)


if __name__ == "__main__":
    main()