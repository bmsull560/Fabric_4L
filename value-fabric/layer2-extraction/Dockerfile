# syntax=docker/dockerfile:1

FROM python:3.11.11-slim-bookworm

# Security: Run as non-root user
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

# Install system dependencies + curl for uv install and healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy dependency files
COPY layer2-extraction/pyproject.toml .
COPY layer2-extraction/uv.lock .

# Install dependencies using uv (creates .venv)
RUN uv sync --frozen

# Copy shared package
COPY shared/ ./shared/

# Copy application code
COPY layer2-extraction/src/ ./src/

# Set PATH to use uv virtual environment and PYTHONPATH for imports
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH=/app:/app/src

# Change ownership to non-root user (including .venv)
RUN chown -R appuser:appgroup /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "src.layer2_extraction.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
