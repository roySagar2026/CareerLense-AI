#!/bin/sh
# Container entrypoint: apply database migrations, then start the API.
# Any arguments replace the default server command (e.g. `pytest`, or uvicorn with --reload).
set -eu

echo "Applying database migrations..."
alembic upgrade head

if [ "$#" -gt 0 ]; then
  exec "$@"
fi
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
