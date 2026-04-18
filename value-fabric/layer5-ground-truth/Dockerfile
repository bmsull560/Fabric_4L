FROM python:3.11.11-slim-bookworm

LABEL maintainer="Value Fabric Engineering"
LABEL description="Layer 5 — Ground Truth Service"

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies directly
RUN pip install --no-cache-dir \
    fastapi>=0.109 \
    uvicorn[standard]>=0.27 \
    sqlalchemy>=2.0 \
    alembic>=1.13 \
    asyncpg>=0.29 \
    psycopg2-binary>=2.9 \
    pydantic>=2.5 \
    pydantic-settings>=2.1 \
    python-multipart>=0.0.6 \
    httpx>=0.26 \
    python-dateutil>=2.9 \
    structlog>=24.1

# Copy shared package
COPY shared/ ./shared/

# Copy source (selective to avoid tests/cache bloat)
COPY layer5-ground-truth/src/ ./src/
COPY layer5-ground-truth/alembic.ini .
COPY layer5-ground-truth/pyproject.toml .

# Set PYTHONPATH so imports work
ENV PYTHONPATH=/app

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8005

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8005/api/v1/health').raise_for_status()"

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8005"]
