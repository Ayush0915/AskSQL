# Use slim Python base image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HF_HUB_DISABLE_SYMLINKS_WARNING=1 \
    SENTENCE_TRANSFORMERS_HOME=/app/cache/sentence-transformers

# Install system dependencies needed for compiling python packages (like psycopg2, chromadb)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory to project root level in container (so `backend/app/main.py` resolution works)
WORKDIR /app

# Copy dependency requirements
COPY backend/requirements.txt /app/backend/requirements.txt

# Install dependencies
RUN pip install --no-cache-dir -r backend/requirements.txt

# Pre-download the SentenceTransformer model to cache it in the Docker image
# This speeds up container startup / runtime retrieval
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Copy the rest of the application files
COPY .env.example /app/.env.example
COPY backend/ /app/backend/

# Copy and setup entrypoint script
COPY backend/entrypoint.sh /app/backend/entrypoint.sh
RUN chmod +x /app/backend/entrypoint.sh

# Expose backend port
EXPOSE 8000

# Set entrypoint
ENTRYPOINT ["/app/backend/entrypoint.sh"]
