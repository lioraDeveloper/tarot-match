#!/usr/bin/env bash
# Start Aether trial app — reachable from phone on the same Wi‑Fi.
set -euo pipefail
cd "$(dirname "$0")/.."

PORT="${PORT:-8000}"
HOST="${HOST:-0.0.0.0}"

if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
pip install -q -r requirements.txt

IP="$(hostname -I 2>/dev/null | awk '{print $1}')"
IP="${IP:-127.0.0.1}"

echo ""
echo "  Aether trial app"
echo "  Local:   http://127.0.0.1:${PORT}"
echo "  Phone:   http://${IP}:${PORT}"
echo "  On phone: open the link → browser menu → Add to Home Screen"
echo ""

exec python -m uvicorn app.main:app --host "$HOST" --port "$PORT" --reload
