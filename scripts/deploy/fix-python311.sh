#!/usr/bin/env bash
# Solo arregla el venv con Python 3.11 (si setup-server.sh falló en pip install)
set -euo pipefail

APP_DIR="${APP_DIR:-/var/www/Findjob/FindJob.lat}"
APP_USER="${APP_USER:-server}"

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Ejecutá con: sudo bash scripts/deploy/fix-python311.sh"
  exit 1
fi

apt-get update -qq
apt-get install -y software-properties-common
if ! command -v python3.11 &>/dev/null; then
  add-apt-repository -y ppa:deadsnakes/ppa
  apt-get update -qq
  apt-get install -y python3.11 python3.11-venv python3.11-dev build-essential libpq-dev
fi

cd "${APP_DIR}"
rm -rf .venv
sudo -u "${APP_USER}" python3.11 -m venv .venv
sudo -u "${APP_USER}" .venv/bin/pip install --upgrade pip
sudo -u "${APP_USER}" .venv/bin/pip install -e .

echo ""
echo "Listo. Python: $(sudo -u ${APP_USER} .venv/bin/python --version)"
echo "Siguiente: bash scripts/deploy/deploy-app.sh"