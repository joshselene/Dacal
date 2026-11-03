# Dockerfile for FastAPI backend (apps/api/Dockerfile)
# Uses Python 3.12 slim image
FROM python:3.12-slim

# Install OS dependencies (curl for health checks, gcc for possible builds)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
 && rm -rf /var/lib/apt/lists/*

# Create a non‑root user
RUN useradd -m appuser
WORKDIR /app

# Copy only pyproject & lock (if any) – for now we install directly via pip
COPY apps/api/pyproject.toml pyproject.toml

# Install Python dependencies
RUN pip install --no-cache-dir fastapi uvicorn[standard] python-dotenv pydantic sqlalchemy asyncpg alembic argon2-cffi python-jose[cryptography] psycopg2-binary redis celery[redis]

# Copy application source
COPY apps/api/app ./app

# Switch to non‑root user
USER appuser

EXPOSE 8000

# Command to run the service
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
