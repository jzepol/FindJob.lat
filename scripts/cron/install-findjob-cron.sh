#!/usr/bin/env bash
# Instala cron jobs para scrape + embeddings (usuario actual, sin sudo).
set -euo pipefail

APP_DIR="${APP_DIR:-/var/www/Findjob/FindJob.lat}"
LOG_DIR="${LOG_DIR:-/var/www/Findjob/logs}"
EMBED_EVERY_MIN="${EMBED_EVERY_MIN:-10}"
EMBED_LIMIT="${EMBED_LIMIT:-10}"

mkdir -p "${LOG_DIR}"
chmod +x "${APP_DIR}/scripts/embed_tick.sh"
chmod +x "${APP_DIR}/scripts/scrape_daily.sh"
chmod +x "${APP_DIR}/scripts/scrape_latam.sh" 2>/dev/null || true

MARKER="# findjob-cron"
TMP="$(mktemp)"

# Quitar bloque anterior si existe
crontab -l 2>/dev/null | grep -v "${MARKER}" | grep -v "findjob" > "${TMP}" || true

cat >> "${TMP}" <<EOF
${MARKER}
# Embeddings: ${EMBED_LIMIT} ofertas cada ${EMBED_EVERY_MIN} min (cuota Gemini free tier)
*/${EMBED_EVERY_MIN} * * * * APP_DIR=${APP_DIR} LOG_DIR=${LOG_DIR} EMBED_LIMIT=${EMBED_LIMIT} bash ${APP_DIR}/scripts/embed_tick.sh
# Scrape liviano diario 03:15 UTC
15 3 * * * APP_DIR=${APP_DIR} LOG_DIR=${LOG_DIR} bash ${APP_DIR}/scripts/scrape_daily.sh
# Scrape LATAM completo domingos 04:00 UTC
0 4 * * 0 APP_DIR=${APP_DIR} LOG_DIR=${LOG_DIR} bash ${APP_DIR}/scripts/scrape_latam.sh >> ${LOG_DIR}/scrape-latam.log 2>&1
EOF

crontab "${TMP}"
rm -f "${TMP}"

echo "Cron instalado:"
crontab -l | grep -A5 "${MARKER}"