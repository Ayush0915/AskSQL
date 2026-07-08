#!/bin/sh

# Exit immediately if a command exits with a non-zero status
set -e

echo "Waiting for PostgreSQL database to start..."
# Use python to check connection availability before starting app
python -c "
import os
import sys
import time
import psycopg2
from urllib.parse import urlparse

admin_url = os.getenv('DATABASE_ADMIN_URL', 'postgresql://postgres@db:5432/postgres')
print(f'Checking admin url: {admin_url}')
# Try connecting up to 15 times
for attempt in range(15):
    try:
        conn = psycopg2.connect(admin_url)
        conn.close()
        print('PostgreSQL is up and accepting connections!')
        sys.exit(0)
    except psycopg2.OperationalError as e:
        print(f'PostgreSQL not ready yet (attempt {attempt+1}/15): {e}')
        time.sleep(2)
sys.exit(1)
"

echo "Seeding the database..."
python -m backend.data.seed_data.seed_db

echo "Embedding the schema metadata into ChromaDB..."
python -m backend.app.rag.embed_schema

echo "Starting FastAPI App..."
exec uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
