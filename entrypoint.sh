#!/bin/sh
set -e

echo "DEBUG: DATABASE_URL is empty? $([ -z "$DATABASE_URL" ] && echo yes || echo no)"
echo "DEBUG: DATABASE_URL contains 'railway'? $(echo "$DATABASE_URL" | grep -q railway && echo yes || echo no)"
echo "DEBUG: DATABASE_URL contains 'localhost'? $(echo "$DATABASE_URL" | grep -q localhost && echo yes || echo no)"
echo "DEBUG: JWT_SECRET_KEY is empty? $([ -z "$JWT_SECRET_KEY" ] && echo yes || echo no)"
echo "DEBUG: PORT is empty? $([ -z "$PORT" ] && echo yes || echo no)"
echo "DEBUG: total env var count: $(env | wc -l)"
echo "DEBUG: all env var names: $(env | cut -d= -f1 | tr '\n' ',')"

uv run --frozen --no-dev alembic upgrade head
exec uv run --frozen --no-dev uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
