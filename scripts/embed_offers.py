#!/usr/bin/env python3
"""Backfill de embeddings para ofertas existentes sin vector.

Uso:
    python scripts/embed_offers.py
    python scripts/embed_offers.py --source remoteok --limit 50
    python scripts/embed_offers.py --force  # re-embedea todas
"""

from __future__ import annotations

import argparse
import asyncio
import sys

import structlog

from app.core.database import async_session_factory
from app.scrapers.registry import list_scrapers
from app.services.embeddings import embed_pending_offers

structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer(),
    ],
)
logger = structlog.get_logger(__name__)


async def run(
    *,
    source: str | None,
    limit: int | None,
    force: bool,
) -> int:
    async with async_session_factory() as session:
        count = await embed_pending_offers(
            session,
            source_slug=source,
            limit=limit,
            force=force,
        )
        await session.commit()

    logger.info("embed_backfill_done", embedded=count, source=source, force=force)
    print(f"\n✓ {count} ofertas embeddeadas\n")
    return 0 if count >= 0 else 1


def main() -> None:
    sources = ", ".join(list_scrapers())
    parser = argparse.ArgumentParser(description="Generar embeddings para ofertas pendientes")
    parser.add_argument("--source", "-s", default=None, choices=list_scrapers(), help=sources)
    parser.add_argument("--limit", type=int, default=None, help="Máximo de ofertas a procesar")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-generar embeddings aunque ya existan",
    )
    args = parser.parse_args()

    try:
        code = asyncio.run(
            run(source=args.source, limit=args.limit, force=args.force),
        )
    except Exception as exc:
        logger.exception("embed_failed", error=str(exc))
        print(f"\n✗ Error: {exc}\n", file=sys.stderr)
        code = 1

    sys.exit(code)


if __name__ == "__main__":
    main()