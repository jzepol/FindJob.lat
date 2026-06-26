#!/usr/bin/env bash
# Scrape masivo LATAM — objetivo ≥1000 ofertas (sin embeddings; correr embed_offers.py después).
#
# Uso en servidor:
#   cd /var/www/Findjob/FindJob.lat
#   nohup bash scripts/scrape_latam.sh > /tmp/scrape-latam.log 2>&1 &
#   tail -f /tmp/scrape-latam.log
set -euo pipefail

APP_DIR="${APP_DIR:-/var/www/Findjob/FindJob.lat}"
cd "${APP_DIR}"
source .venv/bin/activate

LOG="${LOG:-/tmp/scrape-latam.log}"
MAX_PER_RUN="${MAX_PER_RUN:-60}"
SCRAPE_PAUSE_SEC="${SCRAPE_PAUSE_SEC:-3}"
COMMON_FLAGS=(--no-embeddings --no-details)

log() {
  echo "[$(date -Iseconds)] $*" | tee -a "${LOG}"
}

count_offers() {
  python3 - <<'PY'
import asyncio
from sqlalchemy import func, select
from app.core.database import async_session_factory
from app.models.offer import Offer

async def main():
    async with async_session_factory() as session:
        total = await session.execute(select(func.count()).select_from(Offer))
        print(total.scalar() or 0)

asyncio.run(main())
PY
}

run_scrape() {
  local label="$1"
  shift
  log "START ${label}"
  if "$@"; then
    log "OK ${label} — total DB: $(count_offers)"
  else
    log "FAIL ${label} (continuando)"
  fi
  sleep "${SCRAPE_PAUSE_SEC}"
}

preflight_playwright() {
  python3 - <<'PY' >/dev/null 2>&1
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    browser.close()
PY
}

log "=== Findjob LATAM scrape — target ≥1000 ==="
log "Ofertas iniciales: $(count_offers)"

if preflight_playwright; then
  log "Playwright OK — Computrabajo/Bumeran habilitados"
  PLAYWRIGHT_OK=1
else
  log "WARN Playwright no listo — solo RemoteOK (corré: sudo bash scripts/deploy/install-playwright.sh)"
  PLAYWRIGHT_OK=0
fi

# Catálogo completo RemoteOK (~100 ofertas únicas en la API)
run_scrape "remoteok:all" \
  python scripts/scrape.py \
    --source remoteok \
    --keywords "*" \
    --max-results 150 \
    "${COMMON_FLAGS[@]}"

KEYWORDS=(
  "desarrollador"
  "programador"
  "python"
  "javascript"
  "analista"
  "ingeniero software"
  "data"
  "backend"
  "frontend"
  "devops"
)

# ── RemoteOK (remoto global, rápido) ─────────────────────
for kw in "${KEYWORDS[@]}" "software" "full stack" "nodejs"; do
  run_scrape "remoteok:${kw}" \
    python scripts/scrape.py \
      --source remoteok \
      --keywords "${kw}" \
      --max-results 80 \
      "${COMMON_FLAGS[@]}"
done

# ── Computrabajo — AR, CO, MX, PE, CL ────────────────────
declare -A CT_LOCATIONS=(
  [ar]="buenos aires"
  [co]="bogota"
  [mx]="ciudad de mexico"
  [pe]="lima"
  [cl]="santiago"
)

if [[ "${PLAYWRIGHT_OK}" -eq 1 ]]; then
  for country in ar co mx pe cl; do
    location="${CT_LOCATIONS[$country]}"
    for kw in "${KEYWORDS[@]}"; do
      run_scrape "computrabajo:${country}:${kw}" \
        python scripts/scrape.py \
          --source "computrabajo-${country}" \
          --keywords "${kw}" \
          --location "${location}" \
          --max-results "${MAX_PER_RUN}" \
          "${COMMON_FLAGS[@]}"
    done
  done

  # ── Bumeran (Argentina) ──────────────────────────────────
  for kw in "${KEYWORDS[@]}"; do
    run_scrape "bumeran:${kw}" \
      python scripts/scrape.py \
        --source bumeran \
        --keywords "${kw}" \
        --location "buenos aires" \
        --max-results "${MAX_PER_RUN}" \
        "${COMMON_FLAGS[@]}"
  done
else
  log "SKIP computrabajo/bumeran — instalar deps Playwright primero"
fi

log "=== FIN — total ofertas: $(count_offers) ==="