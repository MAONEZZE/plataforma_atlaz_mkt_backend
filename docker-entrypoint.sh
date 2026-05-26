#!/bin/sh
set -e

echo "Running database migrations..."
python -m alembic upgrade head

echo "Testing app import..."
python -c "import app.main; print('import OK')" || exit 1

echo "Starting server (workers=${WEB_CONCURRENCY:-2})..."
exec python -m uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers "${WEB_CONCURRENCY:-2}" \
    --no-access-log
