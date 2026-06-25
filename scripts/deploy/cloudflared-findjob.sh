#!/usr/bin/env bash
# Agrega findjob.lat y api.findjob.lat al túnel Cloudflare existente.
# Ejecutar en el servidor: sudo bash scripts/deploy/cloudflared-findjob.sh
set -euo pipefail

CONFIG="/etc/cloudflared/config.yml"
BACKUP="${CONFIG}.bak.$(date +%Y%m%d%H%M%S)"

if [[ ! -f "${CONFIG}" ]]; then
  echo "ERROR: no existe ${CONFIG}"
  exit 1
fi

if grep -q "hostname: findjob.lat" "${CONFIG}"; then
  echo "findjob.lat ya está en ${CONFIG}"
else
  cp "${CONFIG}" "${BACKUP}"
  echo "Backup: ${BACKUP}"

  python3 - <<'PY'
from pathlib import Path

config = Path("/etc/cloudflared/config.yml")
text = config.read_text()
block = """
  - hostname: findjob.lat
    service: http://localhost:80

  - hostname: www.findjob.lat
    service: http://localhost:80

  - hostname: api.findjob.lat
    service: http://localhost:80
"""
marker = "  - service: http_status:404"
if marker not in text:
    raise SystemExit("No se encontró el bloque catch-all en config.yml")
text = text.replace(marker, block + "\n" + marker)
config.write_text(text)
print("Ingress findjob.lat agregado.")
PY
fi

systemctl restart cloudflared
systemctl status cloudflared --no-pager
echo ""
echo "Verificá en Cloudflare DNS que findjob.lat, www y api apunten al túnel."