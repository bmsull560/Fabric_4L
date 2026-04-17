# Dockerfile for Layer 3: Knowledge Graph & Semantic Layer
FROM python:3.11.11-slim-bookworm

# Security: Create non-root user early
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies (curl needed for HEALTHCHECK)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Install Python dependencies directly
RUN pip install --no-cache-dir \
    fastapi>=0.109 \
    uvicorn[standard]>=0.27 \
    neo4j>=5.15 \
    pinecone-client>=3.0 \
    rdflib>=7.0 \
    sentence-transformers>=2.3 \
    pydantic>=2.5 \
    pydantic-settings>=2.1 \
    python-multipart>=0.0.6 \
    httpx>=0.26 \
    numpy>=1.26 \
    scikit-learn>=1.4 \
    networkx>=3.2 \
    redis>=5.2.0 \
    psutil>=6.0.0

# Copy application code
COPY src/ ./src/

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

# Run the application
CMD ["python", "-m", "uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8001"]
