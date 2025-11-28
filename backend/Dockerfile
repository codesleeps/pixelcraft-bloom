# Multi-stage Dockerfile for FastAPI backend
# Builder stage: install build deps and build wheels
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       gcc \
       build-essential \
       libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and build wheels to avoid reinstalling when app code changes
COPY backend/requirements.txt ./requirements.txt

# Build wheels for faster, repeatable installs
RUN python -m pip install --upgrade pip setuptools wheel \
    && pip wheel --no-cache-dir --no-deps -r requirements.txt -w /wheels


# Runtime image: minimal, non-root user
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Create a non-root user for security
RUN groupadd --system appuser && useradd --system --gid appuser --create-home --home-dir /home/appuser appuser

WORKDIR /app

# Copy wheels and requirements from builder
COPY --from=builder /wheels /wheels
COPY backend/requirements.txt ./requirements.txt

# Install deps from wheels for deterministic installs, then ensure pydantic[email]
RUN python -m pip install --upgrade pip \
    && pip install --no-cache-dir /wheels/* \
    && pip install --no-cache-dir "pydantic[email]"

# Copy application code
COPY backend/ .

# Give the app user ownership of the app directory
RUN chown -R appuser:appuser /app

# Expose the port the app uses
EXPOSE 8000

# Switch to non-root user
USER appuser

# Development-friendly default command (with reload). For production, override to remove --reload.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
