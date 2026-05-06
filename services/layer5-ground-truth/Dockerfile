# syntax=docker/dockerfile:1
FROM python:3.11.11-slim-bookworm@sha256:081075da77b2b55c23c088251026fb69a7b2bf92471e491ff5fd75c192fd38e5

LABEL maintainer="Value Fabric Engineering"
LABEL description="Layer 5 — Ground Truth Service"

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv from official image
COPY --from=ghcr.io/astral-sh/uv:0.11.6 /uv /uvx /bin/

WORKDIR /app

# Copy dependency files first (for better layer caching)
COPY pyproject.toml uv.lock ./

# Install dependencies using uv (deterministic from lock file)
RUN uv sync --frozen --no-install-project

# Copy source (selective to avoid tests/cache bloat)
COPY src/ ./src/
COPY ../../value_fabric/ ./value_fabric/
COPY alembic.ini .

# Set PATH to use uv virtual environment and PYTHONPATH for imports
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH=/app:/app/src

# Create non-root user
RUN groupadd -r appgroup && useradd -r -g appgroup -m appuser && chown -R appuser:appgroup /app
USER appuser

EXPOSE 8005

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8005/health || exit 1

CMD ["uvicorn", "src.layer5_ground_truth.api.main:app", "--host", "0.0.0.0", "--port", "8005"]
