#!/usr/bin/env bash
# Production-style launcher used on the VM: gunicorn supervising uvicorn workers.
set -euo pipefail

WORKERS="${WEB_CONCURRENCY:-2}"
exec gunicorn app.main:app \
  --worker-class uvicorn.workers.UvicornWorker \
  --workers "$WORKERS" \
  --bind 0.0.0.0:"${PORT:-8000}" \
  --access-logfile -
