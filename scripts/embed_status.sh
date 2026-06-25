#!/usr/bin/env bash
# Muestra cuántas ofertas faltan embeddear.
set -euo pipefail
APP_DIR="${APP_DIR:-/var/www/Findjob/FindJob.lat}"
cd "${APP_DIR}"
source .venv/bin/activate

python3 - <<'PY'
import asyncio
from sqlalchemy import func, select
from app.core.database import async_session_factory
from app.models.offer import Offer

async def main():
    async with async_session_factory() as session:
        total = (await session.execute(select(func.count()).select_from(Offer))).scalar() or 0
        pending = (
            await session.execute(
                select(func.count()).select_from(Offer).where(Offer.embedding.is_(None))
            )
        ).scalar() or 0
        done = total - pending
        pct = round(100 * done / total, 1) if total else 0
        print(f"Ofertas: {total} total | {done} embeddeadas | {pending} pendientes ({pct}%)")
        if pending and pending > 0:
            # ~10 cada 10 min
            mins = pending * 10
            print(f"Estimado con cron (10/10min): ~{mins // 60}h {mins % 60}m")

asyncio.run(main())
PY