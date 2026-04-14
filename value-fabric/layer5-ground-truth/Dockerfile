FROM python:3.11-slim

LABEL maintainer="Value Fabric Engineering"
LABEL description="Layer 5 — Ground Truth Service"

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -e ".[dev]"

# Copy source
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8005

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8005/api/v1/health').raise_for_status()"

CMD ["uvicorn", "layer5_ground_truth.api.main:app", "--host", "0.0.0.0", "--port", "8005"]
