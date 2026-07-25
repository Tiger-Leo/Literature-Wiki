#!/usr/bin/env bash
# serve.sh — run the RAG API (background) + the Next.js frontend (foreground).
#
# Domain-agnostic, no absolute paths: resolves the repo root from this script's
# location. Loads .env if present, rebuilds the frontend search index, starts
# uvicorn in the background, waits for /health, then runs the web dev server.
# Ctrl-C (SIGINT/SIGTERM) cleanly stops the background API.
#
# Usage:   bash scripts/serve.sh          # api + `pnpm dev`
#          WEB_MODE=start bash scripts/serve.sh   # api + `pnpm start` (prod build)
set -euo pipefail

# --- locate repo root (parent of scripts/) ---------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

# --- load .env if present --------------------------------------------------
if [[ -f .env ]]; then
  echo ">> Loading .env"
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

PY="${PYTHON:-python}"
RAG_HOST="${RAG_HOST:-0.0.0.0}"
RAG_PORT="${RAG_PORT:-8000}"
WEB_MODE="${WEB_MODE:-dev}"          # dev | start
# Health check hits localhost regardless of bind host.
HEALTH_URL="http://127.0.0.1:${RAG_PORT}/health"
API_LOG="$(mktemp -t litwiki-api.XXXXXX.log)"

API_PID=""
cleanup() {
  if [[ -n "${API_PID}" ]] && kill -0 "${API_PID}" 2>/dev/null; then
    echo ">> Stopping API (pid ${API_PID})"
    kill "${API_PID}" 2>/dev/null || true
    wait "${API_PID}" 2>/dev/null || true
  fi
}
trap cleanup INT TERM EXIT

# --- preflight tool checks -------------------------------------------------
if ! "${PY}" -c "import uvicorn" 2>/dev/null; then
  echo "!! uvicorn not importable under '${PY}'. Run 'make install' or activate your env." >&2
  exit 1
fi
if ! command -v pnpm >/dev/null 2>&1; then
  echo "!! pnpm not found. Install pnpm: https://pnpm.io/installation" >&2
  exit 1
fi

# --- build the frontend search index --------------------------------------
echo ">> Building frontend search index (scripts/export_wiki.py)"
"${PY}" scripts/export_wiki.py || echo "!! export_wiki.py failed (continuing; check wiki/ exists)"

# --- start the API in the background ---------------------------------------
echo ">> Starting API on ${RAG_HOST}:${RAG_PORT} (logs: ${API_LOG})"
"${PY}" -m uvicorn rag.server:app --host "${RAG_HOST}" --port "${RAG_PORT}" \
  >"${API_LOG}" 2>&1 &
API_PID=$!

# --- wait for /health ------------------------------------------------------
echo -n ">> Waiting for API /health "
ready=""
for _ in $(seq 1 60); do
  if ! kill -0 "${API_PID}" 2>/dev/null; then
    echo ""
    echo "!! API process exited early. Last log lines:" >&2
    tail -n 30 "${API_LOG}" >&2 || true
    exit 1
  fi
  if curl -fsS "${HEALTH_URL}" >/dev/null 2>&1; then
    ready="yes"
    break
  fi
  echo -n "."
  sleep 1
done
echo ""
if [[ -z "${ready}" ]]; then
  echo "!! API did not become healthy at ${HEALTH_URL}. Last log lines:" >&2
  tail -n 30 "${API_LOG}" >&2 || true
  exit 1
fi
echo ">> API healthy."

# --- run the frontend (foreground) -----------------------------------------
echo ">> Starting frontend (pnpm ${WEB_MODE}) in web/"
cd web
if [[ "${WEB_MODE}" == "start" ]]; then
  pnpm start
else
  pnpm dev
fi
