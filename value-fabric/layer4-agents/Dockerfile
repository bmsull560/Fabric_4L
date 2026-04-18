# Multi-stage build for Layer 4: Agentic Workflow Engine
# Stage 1: Builder - compiles dependencies
FROM python:3.11.11-slim-bookworm AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies to system site-packages
COPY layer4-agents/pyproject.toml .
COPY layer4-agents/README.md .
RUN mkdir -p src && touch src/__init__.py && pip install --no-cache-dir . && rm -rf src README.md pyproject.toml

# Stage 2: Runtime - minimal image with only runtime libraries
FROM python:3.11.11-slim-bookworm AS runtime

# Install only runtime library (libpq for psycopg2)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user with home directory
RUN groupadd -r appgroup && useradd -r -g appgroup -m appuser

WORKDIR /app

# Copy installed packages from builder (site-packages location)
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Ensure PATH includes local bin
ENV PATH=/usr/local/bin:$PATH
ENV PYTHONPATH=/usr/local/lib/python3.11/site-packages:/app

# Copy shared package
COPY shared/ ./shared/

# Copy source code
COPY layer4-agents/src/ ./src/

# Change ownership
RUN chown -R appuser:appgroup /app /home/appuser

# Switch to non-root user
USER appuser

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Expose API port
EXPOSE 8000

# Health check using Python (requests is installed)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Run the API server
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
