#!/usr/bin/env bash
# Ejecutar en el servidor con: sudo bash scripts/deploy/setup-server.sh
set -euo pipefail

APP_DIR="${APP_DIR:-/var/www/Findjob/FindJob.lat}"
APP_USER="${APP_USER:-server}"
DB_NAME="${DB_NAME:-findjob}"
DB_USER="${DB_USER:-findjob}"
WEB_PORT="${WEB_PORT:-3001}"
API_PORT="${API_PORT:-8000}"

PG_VERSION="$(psql --version | grep -oP '\d+' | head -1)"

install_pgvector() {
  echo "==> pgvector (PostgreSQL ${PG_VERSION})"
  local pkg="postgresql-${PG_VERSION}-pgvector"
  if apt-cache show "${pkg}" &>/dev/null; then
    apt-get install -y "${pkg}"
    return
  fi
  echo "    Paquete ${pkg} no disponible — compilando desde fuente..."
  apt-get install -y git "postgresql-server-dev-${PG_VERSION}"
  local build_dir="/tmp/pgvector-build-$$"
  rm -rf "${build_dir}"
  git clone --depth 1 --branch v0.7.4 https://github.com/pgvector/pgvector.git "${build_dir}"
  cd "${build_dir}"
  make
  make install
  cd /
  rm -rf "${build_dir}"
  echo "    pgvector compilado e instalado."
}

PYTHON_BIN="python3.11"

echo "==> Paquetes del sistema"
apt-get update -qq
apt-get install -y software-properties-common build-essential libpq-dev git curl
if ! command -v "${PYTHON_BIN}" &>/dev/null; then
  echo "    Instalando Python 3.11 (deadsnakes)..."
  add-apt-repository -y ppa:deadsnakes/ppa
  apt-get update -qq
  apt-get install -y python3.11 python3.11-venv python3.11-dev
fi
install_pgvector

echo "==> Usuario y base PostgreSQL"
DB_PASS="${FINDJOB_DB_PASS:-$(openssl rand -hex 16)}"
sudo -u postgres psql -tc "SELECT 1 FROM pg_roles WHERE rolname='${DB_USER}'" | grep -q 1 \
  || sudo -u postgres psql -c "CREATE USER ${DB_USER} WITH PASSWORD '${DB_PASS}';"
sudo -u postgres psql -c "ALTER USER ${DB_USER} WITH PASSWORD '${DB_PASS}';" 2>/dev/null || true
sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname='${DB_NAME}'" | grep -q 1 \
  || sudo -u postgres psql -c "CREATE DATABASE ${DB_NAME} OWNER ${DB_USER};"
sudo -u postgres psql -d "${DB_NAME}" -c "CREATE EXTENSION IF NOT EXISTS vector;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME} TO ${DB_USER};"
sudo -u postgres psql -d "${DB_NAME}" -c "GRANT ALL ON SCHEMA public TO ${DB_USER};"

echo "==> Python venv + dependencias (${PYTHON_BIN})"
cd "${APP_DIR}"
rm -rf .venv
sudo -u "${APP_USER}" "${PYTHON_BIN}" -m venv .venv
sudo -u "${APP_USER}" .venv/bin/pip install --upgrade pip
sudo -u "${APP_USER}" .venv/bin/pip install -e .

echo "==> systemd (solo API — frontend con PM2)"
cp "${APP_DIR}/scripts/deploy/findjob-api.service" /etc/systemd/system/
sed -i "s|__APP_DIR__|${APP_DIR}|g; s|__APP_USER__|${APP_USER}|g; s|__WEB_PORT__|${WEB_PORT}|g" \
  /etc/systemd/system/findjob-api.service
systemctl daemon-reload
systemctl enable findjob-api

echo "==> nginx"
cp "${APP_DIR}/scripts/deploy/nginx-findjob.conf" /etc/nginx/sites-available/findjob
ln -sf /etc/nginx/sites-available/findjob /etc/nginx/sites-enabled/findjob
nginx -t
systemctl reload nginx

DB_URL="postgresql+asyncpg://${DB_USER}:${DB_PASS}@localhost:5432/${DB_NAME}"
if [[ -f "${APP_DIR}/.env" ]]; then
  if grep -q '^DATABASE_URL=' "${APP_DIR}/.env"; then
    sed -i "s|^DATABASE_URL=.*|DATABASE_URL=${DB_URL}|" "${APP_DIR}/.env"
  else
    echo "DATABASE_URL=${DB_URL}" >> "${APP_DIR}/.env"
  fi
  chown "${APP_USER}:${APP_USER}" "${APP_DIR}/.env"
fi

echo ""
echo "Listo."
echo "  DATABASE_URL=${DB_URL}"
echo "  Frontend: puerto ${WEB_PORT} | API: puerto ${API_PORT}"
echo ""
echo "Siguiente (como ${APP_USER}):"
echo "  cd ${APP_DIR} && bash scripts/deploy/deploy-app.sh"
echo "  pm2 startup   # una vez, para que findjob-web arranque al boot"