# syntax=docker/dockerfile:1

FROM python:3.11.11-slim-bookworm

# Security: Run as non-root user
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies directly (avoid editable install issues)
RUN pip install --no-cache-dir \
    fastapi>=0.115.0 \
    uvicorn[standard]>=0.32.0 \
    pydantic>=2.9.0 \
    openai>=1.40.0 \
    langchain>=0.3.0 \
    langchain-text-splitters>=0.3.0 \
    rdflib>=7.1.0 \
    numpy>=1.26.0 \
    redis>=5.2.0 \
    celery>=5.4.0 \
    httpx>=0.27.0 \
    python-dotenv>=1.0.0 \
    prometheus-client>=0.21.0 \
    psutil>=6.0.0

# Copy shared package
COPY shared/ ./shared/

# Copy application code
COPY layer2-extraction/src/ ./src/

# Set PYTHONPATH so imports work
ENV PYTHONPATH=/app:/app/src

# Change ownership to non-root user
RUN chown -R appuser:appgroup /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "src.layer2_extraction.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
