#!/usr/bin/env bash
# Sincroniza contraseña PostgreSQL del usuario findjob con .env
# Ejecutar: sudo bash scripts/deploy/fix-db-password.sh
set -euo pipefail

APP_DIR="${APP_DIR:-/var/www/Findjob/FindJob.lat}"
APP_USER="${APP_USER:-server}"
DB_NAME="${DB_NAME:-findjob}"
DB_USER="${DB_USER:-findjob}"
ENV_FILE="${APP_DIR}/.env"

DB_PASS="${FINDJOB_DB_PASS:-$(openssl rand -hex 16)}"

echo "==> Usuario PostgreSQL '${DB_USER}'"
sudo -u postgres psql -tc "SELECT 1 FROM pg_roles WHERE rolname='${DB_USER}'" | grep -q 1 \
  || sudo -u postgres psql -c "CREATE USER ${DB_USER} WITH PASSWORD '${DB_PASS}';"
sudo -u postgres psql -c "ALTER USER ${DB_USER} WITH PASSWORD '${DB_PASS}';"

sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname='${DB_NAME}'" | grep -q 1 \
  || sudo -u postgres psql -c "CREATE DATABASE ${DB_NAME} OWNER ${DB_USER};"

sudo -u postgres psql -d "${DB_NAME}" -c "CREATE EXTENSION IF NOT EXISTS vector;" 2>/dev/null || true
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME} TO ${DB_USER};"
sudo -u postgres psql -d "${DB_NAME}" -c "GRANT ALL ON SCHEMA public TO ${DB_USER};"
sudo -u postgres psql -d "${DB_NAME}" -c "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO ${DB_USER};"

DB_URL="postgresql+asyncpg://${DB_USER}:${DB_PASS}@localhost:5432/${DB_NAME}"

if [[ -f "${ENV_FILE}" ]]; then
  if grep -q '^DATABASE_URL=' "${ENV_FILE}"; then
    sed -i "s|^DATABASE_URL=.*|DATABASE_URL=${DB_URL}|" "${ENV_FILE}"
  else
    echo "DATABASE_URL=${DB_URL}" >> "${ENV_FILE}"
  fi
  chown "${APP_USER}:${APP_USER}" "${ENV_FILE}"
  chmod 600 "${ENV_FILE}"
fi

echo ""
echo "Listo. Contraseña sincronizada en .env y PostgreSQL."
echo "  DATABASE_URL=${DB_URL}"
echo ""
echo "Siguiente:"
echo "  cd ${APP_DIR} && bash scripts/deploy/deploy-app.sh"