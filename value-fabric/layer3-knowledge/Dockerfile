# Dockerfile for Layer 3: Knowledge Graph & Semantic Layer
# Using uv for deterministic builds from lock file
# Python 3.11.11 slim image with SHA digest for reproducibility
FROM python:3.11.11-slim-bookworm@sha256:081075da77b2b55c23c088251026fb69a7b2bf92471e491ff5fd75c192fd38e5

# Security: Create non-root user early
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_NO_CACHE=1

# Install system dependencies (curl needed for HEALTHCHECK)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast, reproducible Python package management
# Pinned to v0.11.6 for build reproducibility
COPY --from=ghcr.io/astral-sh/uv:0.11.6 /uv /uvx /bin/

# Set work directory
WORKDIR /app

# Copy lock file and pyproject.toml for dependency installation
COPY layer3-knowledge/pyproject.toml layer3-knowledge/uv.lock ./

# Install dependencies using uv (reproducible from lock file)
RUN uv sync --frozen --no-install-project

# Copy shared package
COPY shared/ ./shared/

# Copy application code
COPY layer3-knowledge/src/ ./src/

# Set PYTHONPATH so imports work
ENV PYTHONPATH=/app

# Change ownership to non-root user
RUN chown -R appuser:appgroup /app

# Switch to non-root user before runtime
USER appuser

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Run the application using uv run for proper environment
CMD ["uv", "run", "python", "-m", "uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8001"]
