#!/usr/bin/env bash
# Scrape incremental diario (más liviano que scrape_latam.sh).
set -euo pipefail

APP_DIR="${APP_DIR:-/var/www/Findjob/FindJob.lat}"
LOG_DIR="${LOG_DIR:-/var/www/Findjob/logs}"
mkdir -p "${LOG_DIR}"

cd "${APP_DIR}"
source .venv/bin/activate

LOG="${LOG_DIR}/scrape-daily.log"
MAX="${MAX_PER_RUN:-40}"
FLAGS=(--no-embeddings --no-details)

log() { echo "[$(date -Iseconds)] $*" | tee -a "${LOG}"; }

KEYWORDS=(python desarrollador backend devops data)
COUNTRIES=(ar co mx pe cl)
LOCATIONS=(buenos+aires bogota "ciudad de mexico" lima santiago)

log "=== scrape daily ==="

for kw in "${KEYWORDS[@]}"; do
  log "remoteok:${kw}"
  python scripts/scrape.py -s remoteok -k "${kw}" --max-results 50 "${FLAGS[@]}" >> "${LOG}" 2>&1 || true
  sleep 3
done

for i in "${!COUNTRIES[@]}"; do
  country="${COUNTRIES[$i]}"
  location="${LOCATIONS[$i]}"
  export COMPUTRABAJO_COUNTRY="${country}"
  for kw in "${KEYWORDS[@]}"; do
    log "computrabajo:${country}:${kw}"
    python scripts/scrape.py -s computrabajo -k "${kw}" -l "${location}" \
      --max-results "${MAX}" "${FLAGS[@]}" >> "${LOG}" 2>&1 || true
    sleep 5
  done
done

log "=== fin daily ==="