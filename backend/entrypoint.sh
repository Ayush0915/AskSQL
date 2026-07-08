#!/bin/sh

# Exit immediately if a command exits with a non-zero status
set -e

echo "Starting FastAPI App with DuckDB..."
exec uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
