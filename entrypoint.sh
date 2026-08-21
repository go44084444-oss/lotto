#!/bin/sh
set -e

echo "DEBUG: DATABASE_URL is empty? $([ -z "$DATABASE_URL" ] && echo yes || echo no)"
echo "DEBUG: DATABASE_URL contains 'railway'? $(echo "$DATABASE_URL" | grep -q railway && echo yes || echo no)"
echo "DEBUG: DATABASE_URL contains 'localhost'? $(echo "$DATABASE_URL" | grep -q localhost && echo yes || echo no)"

uv run --frozen --no-dev alembic upgrade head
exec uv run --frozen --no-dev uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
