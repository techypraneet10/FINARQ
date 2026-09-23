#!/bin/sh
set -e

# ==============================================================================
# Financial RAG Platform - Container Entrypoint
# Supports modes:
#   - 'api'     : Starts FastAPI ASGI Server with Uvicorn
#   - 'worker'  : Starts Ingestion Background Worker Daemon
#   - 'migrate' : Runs Alembic Database Migrations
#   - '*'       : Executes custom arbitrary command
# ==============================================================================

MODE="${1:-api}"

case "$MODE" in
  api)
    echo "[Entrypoint] Starting FastAPI Application Service..."
    exec uvicorn financial_rag.main:app \
      --host "${APP_HOST:-0.0.0.0}" \
      --port "${APP_PORT:-8000}" \
      --timeout-graceful-shutdown "${APP_SHUTDOWN_TIMEOUT_SECONDS:-15}"
    ;;

  worker)
    echo "[Entrypoint] Starting Ingestion Worker Daemon..."
    exec python -m financial_rag.worker
    ;;

  migrate)
    echo "[Entrypoint] Executing Database Migrations..."
    exec python scripts/migrate.py
    ;;

  *)
    echo "[Entrypoint] Executing custom command: $@"
    exec "$@"
    ;;
esac
