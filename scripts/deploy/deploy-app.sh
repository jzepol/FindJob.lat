#!/usr/bin/env bash
# Sin sudo — actualizar código, migrar DB, build frontend, reiniciar servicios
set -euo pipefail

APP_DIR="${APP_DIR:-/var/www/Findjob/FindJob.lat}"
cd "${APP_DIR}"

echo "==> git pull"
git pull --ff-only

echo "==> backend deps"
if [[ ! -f .venv/bin/activate ]]; then
  echo "ERROR: no existe .venv — corré primero: sudo bash scripts/deploy/setup-server.sh"
  exit 1
fi
source .venv/bin/activate
pip install -e .

echo "==> migraciones"
alembic upgrade head

echo "==> frontend build"
cd frontend
npm ci
set -a && source .env.production && set +a
npm run build

echo "==> reiniciar frontend (pm2)"
mkdir -p logs
# Liberar puerto si quedó un next manual colgado de un deploy anterior
fuser -k "${WEB_PORT:-3001}"/tcp 2>/dev/null || true
sleep 1
if pm2 describe findjob-web >/dev/null 2>&1; then
  pm2 delete findjob-web 2>/dev/null || true
fi
pm2 start ecosystem.config.cjs --env production
pm2 save
cd ..

echo "==> reiniciar API (requiere sudo si usás systemd)"
if systemctl is-enabled findjob-api >/dev/null 2>&1; then
  sudo systemctl restart findjob-api
  sudo systemctl status findjob-api --no-pager
else
  echo "    findjob-api no está en systemd — levantá la API manualmente o con setup-server.sh"
fi