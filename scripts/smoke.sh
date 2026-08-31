#!/usr/bin/env bash
set -euo pipefail

port="${PORT:-8012}"
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port "$port" > /tmp/what-needs-me-smoke.log 2>&1 &
server_pid=$!
cleanup() { kill "$server_pid" 2>/dev/null || true; wait "$server_pid" 2>/dev/null || true; }
trap cleanup EXIT

for _ in {1..30}; do
  if curl --fail --silent "http://127.0.0.1:$port/api/health" >/dev/null; then break; fi
  sleep 0.2
done

curl --fail --silent "http://127.0.0.1:$port/api/health" | .venv/bin/python -m json.tool
curl --fail --silent "http://127.0.0.1:$port/api/accounts" | .venv/bin/python -m json.tool >/dev/null
curl --fail --silent "http://127.0.0.1:$port/api/today?days=7" > /tmp/what-needs-me-today.json
.venv/bin/python -c 'import json; d=json.load(open("/tmp/what-needs-me-today.json")); print("today cards:", len(d["cards"]))'
