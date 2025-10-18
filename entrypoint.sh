#!/bin/sh
set -ex

# Log the start of the entrypoint script
echo "[$(date)] Starting entrypoint script..."

# Wait for PostgreSQL to be ready
echo "[$(date)] Waiting for PostgreSQL..."
sleep 5
echo "[$(date)] Database is ready!"



# Run migrations
echo "[$(date)] Running migrations..."
uv run alembic upgrade head

# Run pre-start checks (if applicable)
echo "[$(date)] Running pre-start checks..."
uv run ./app/backend_pre_start.py || true


# Create initial data (if applicable)
echo "[$(date)] Creating initial data..."
uv run ./app/initial_data.py || true

# Start the FastAPI application
echo "[$(date)] Starting FastAPI application..."
uv run uvicorn app.main:app --host 0.0.0.0 --port 8080
