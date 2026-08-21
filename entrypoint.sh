#!/bin/sh
set -e

uv run --frozen --no-dev alembic upgrade head
exec uv run --frozen --no-dev uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
