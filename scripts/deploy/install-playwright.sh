#!/usr/bin/env bash
# Playwright + Chromium para scrapers (Computrabajo, Bumeran).
# Ejecutar en el servidor:
#   bash scripts/deploy/install-playwright.sh
# Si falla por librerías: sudo bash scripts/deploy/install-playwright.sh
set -euo pipefail

APP_DIR="${APP_DIR:-/var/www/Findjob/FindJob.lat}"
cd "${APP_DIR}"
source .venv/bin/activate

echo "==> playwright browsers"
playwright install chromium

if command -v sudo >/dev/null && sudo -n true 2>/dev/null; then
  echo "==> dependencias del sistema (sudo)"
  sudo playwright install-deps chromium
else
  echo "==> Sin sudo: corré manualmente:"
  echo "    sudo \$(which playwright) install-deps chromium"
fi

echo "==> test rápido computrabajo AR"
COMPUTRABAJO_COUNTRY=ar python scripts/scrape.py \
  -s computrabajo -k desarrollador -l "buenos aires" \
  --max-results 5 --no-embeddings --no-details

echo "Listo."