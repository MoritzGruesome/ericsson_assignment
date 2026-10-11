#!/usr/bin/env bash

set -Eeuo pipefail

PEOPLEGUIDE_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PEOPLEGUIDE_VENV="$PEOPLEGUIDE_ROOT/.venv"
PEOPLEGUIDE_ENV_FILE="$PEOPLEGUIDE_ROOT/.env"
PEOPLEGUIDE_QDRANT_COLLECTION="$PEOPLEGUIDE_ROOT/.data/qdrant/collection/peopleguide-policies"
PEOPLEGUIDE_PYTHON_BIN="${PEOPLEGUIDE_PYTHON_BIN:-python3.12}"
PEOPLEGUIDE_REINDEX=false

case "${1:-}" in
  "") ;;
  --reindex) PEOPLEGUIDE_REINDEX=true ;;
  -h|--help)
    echo "Usage: ./setup.sh [--reindex]"
    echo "Set up PeopleGuide and run the FastAPI and React development servers."
    exit 0
    ;;
  *)
    echo "Usage: ./setup.sh [--reindex]" >&2
    exit 2
    ;;
esac

if ! command -v "$PEOPLEGUIDE_PYTHON_BIN" >/dev/null 2>&1; then
  echo "Python 3.12 is required. Set PEOPLEGUIDE_PYTHON_BIN if it has another command name." >&2
  exit 1
fi

if ! "$PEOPLEGUIDE_PYTHON_BIN" -c 'import sys; raise SystemExit(sys.version_info < (3, 12))'; then
  echo "Python 3.12 or later is required." >&2
  exit 1
fi

if ! command -v node >/dev/null 2>&1 || ! command -v npm >/dev/null 2>&1; then
  echo "Node.js 20 or later and npm are required." >&2
  exit 1
fi

PEOPLEGUIDE_NODE_MAJOR="$(node -p 'process.versions.node.split(".")[0]')"
if (( PEOPLEGUIDE_NODE_MAJOR < 20 )); then
  echo "Node.js 20 or later is required; found $(node --version)." >&2
  exit 1
fi

if [[ ! -f "$PEOPLEGUIDE_ENV_FILE" ]]; then
  cp "$PEOPLEGUIDE_ROOT/.env.example" "$PEOPLEGUIDE_ENV_FILE"
  echo "Created .env from .env.example."
fi

if ! grep -Eq '^OPENAI_API_KEY=.+$' "$PEOPLEGUIDE_ENV_FILE"; then
  echo "Set OPENAI_API_KEY in $PEOPLEGUIDE_ENV_FILE, then run ./setup.sh again." >&2
  exit 1
fi

if [[ ! -x "$PEOPLEGUIDE_VENV/bin/python" ]]; then
  echo "Creating Python virtual environment..."
  "$PEOPLEGUIDE_PYTHON_BIN" -m venv "$PEOPLEGUIDE_VENV"
fi

echo "Installing backend dependencies..."
"$PEOPLEGUIDE_VENV/bin/pip" install -e "$PEOPLEGUIDE_ROOT/backend[dev]"

echo "Installing frontend dependencies..."
(
  cd "$PEOPLEGUIDE_ROOT/frontend"
  npm install
)

if [[ "$PEOPLEGUIDE_REINDEX" == true || ! -d "$PEOPLEGUIDE_QDRANT_COLLECTION" ]]; then
  echo "Building the policy index..."
  (
    cd "$PEOPLEGUIDE_ROOT/backend"
    PYTHONPATH=. "$PEOPLEGUIDE_VENV/bin/python" -m app.scripts.ingest_policies
  )
else
  echo "Policy index already exists; use ./setup.sh --reindex to rebuild it."
fi

PEOPLEGUIDE_BACKEND_PID=""
PEOPLEGUIDE_FRONTEND_PID=""

cleanup() {
  trap - EXIT INT TERM
  echo
  echo "Stopping PeopleGuide..."
  if [[ -n "$PEOPLEGUIDE_BACKEND_PID" ]]; then
    kill "$PEOPLEGUIDE_BACKEND_PID" 2>/dev/null || true
  fi
  if [[ -n "$PEOPLEGUIDE_FRONTEND_PID" ]]; then
    kill "$PEOPLEGUIDE_FRONTEND_PID" 2>/dev/null || true
  fi
  wait "$PEOPLEGUIDE_BACKEND_PID" "$PEOPLEGUIDE_FRONTEND_PID" 2>/dev/null || true
}

trap cleanup EXIT INT TERM

echo "Starting FastAPI at http://localhost:8000..."
(
  cd "$PEOPLEGUIDE_ROOT/backend"
  export PYTHONPATH=.
  exec "$PEOPLEGUIDE_VENV/bin/uvicorn" app.main:app --reload --port 8000
) &
PEOPLEGUIDE_BACKEND_PID=$!

echo "Starting React at http://localhost:5173..."
(
  cd "$PEOPLEGUIDE_ROOT/frontend"
  exec npm run dev
) &
PEOPLEGUIDE_FRONTEND_PID=$!

echo
echo "PeopleGuide is running. Open http://localhost:5173"
echo "Press Ctrl+C to stop both servers."

wait "$PEOPLEGUIDE_BACKEND_PID" "$PEOPLEGUIDE_FRONTEND_PID"
