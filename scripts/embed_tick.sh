#!/usr/bin/env bash
# Un "tick" de embeddings: procesa hasta EMBED_LIMIT ofertas (default 10).
# Pensado para cron cada 10 min — respeta cuota free tier de Gemini.
set -euo pipefail

APP_DIR="${APP_DIR:-/var/www/Findjob/FindJob.lat}"
LOG_DIR="${LOG_DIR:-/var/www/Findjob/logs}"
EMBED_LIMIT="${EMBED_LIMIT:-10}"

mkdir -p "${LOG_DIR}"
cd "${APP_DIR}"
source .venv/bin/activate

LOG="${LOG_DIR}/embed-tick.log"
echo "[$(date -Iseconds)] tick limit=${EMBED_LIMIT}" >> "${LOG}"

python scripts/embed_offers.py --limit "${EMBED_LIMIT}" >> "${LOG}" 2>&1 || {
  code=$?
  echo "[$(date -Iseconds)] exit=${code}" >> "${LOG}"
  exit 0
}

echo "[$(date -Iseconds)] ok" >> "${LOG}"