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
cd ..

echo "==> reiniciar servicios (requiere sudo)"
sudo systemctl restart findjob-api findjob-web
sudo systemctl status findjob-api findjob-web --no-pager