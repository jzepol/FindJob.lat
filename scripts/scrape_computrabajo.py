#!/usr/bin/env python3
"""Script manual para scrapear Computrabajo y persistir ofertas.

Uso:
    python scripts/scrape_computrabajo.py -k "desarrollador python" -l "buenos aires"
    python scripts/scrape_computrabajo.py -k "desarrollador python" --no-details  # solo listado
"""

from __future__ import annotations

import argparse
import asyncio
import sys

import structlog

from app.core.database import async_session_factory
from app.scrapers.computrabajo import ComputrabajoScraper
from app.scrapers.schemas import IngestResult, ScrapeParams
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
    keywords: str,
    location: str,
    *,
    fetch_details: bool,
    max_results: int | None,
) -> int:
    scraper = ComputrabajoScraper()
    params = ScrapeParams(
        keywords=keywords,
        location=location,
        fetch_details=fetch_details,
        max_results=max_results,
    )

    logger.info(
        "scrape_start",
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
        source = await ensure_source(session, scraper.slug)
        scrape_run = await create_scrape_run(session, source.id)

        try:
            result = await ingest_offers(session, source=source, raw_offers=raw_offers)
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

    logger.info("scrape_done", found=result.found, new=result.new, updated=result.updated)
    print(
        f"\n✓ {result.found} ofertas — {result.new} nuevas, {result.updated} actualizadas"
        f" ({with_description} con descripción)\n"
    )
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Scrapear Computrabajo y guardar en PostgreSQL")
    parser.add_argument("--keywords", "-k", required=True, help='Ej: "desarrollador python"')
    parser.add_argument("--location", "-l", default="", help='Ej: "buenos aires"')
    parser.add_argument(
        "--no-details",
        action="store_true",
        help="Solo listado, sin visitar páginas de detalle",
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=None,
        help="Máximo de ofertas del listado (default: SCRAPER_MAX_RESULTS)",
    )
    args = parser.parse_args()

    try:
        code = asyncio.run(
            run(
                args.keywords,
                args.location,
                fetch_details=not args.no_details,
                max_results=args.max_results,
            )
        )
    except Exception as exc:
        logger.exception("scrape_failed", error=str(exc))
        print(f"\n✗ Error: {exc}\n", file=sys.stderr)
        code = 1

    sys.exit(code)


if __name__ == "__main__":
    main()