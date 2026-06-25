#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
source .venv/bin/activate 2>/dev/null || true
export OAUTHLIB_INSECURE_TRANSPORT=1
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload