FROM python:3.11.11-slim-bookworm

# Security: Create non-root user early
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

WORKDIR /app

# Install curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Install Python dependencies directly
RUN pip install --no-cache-dir \
    fastapi>=0.115.0 \
    uvicorn[standard]>=0.32.0 \
    pydantic>=2.9.0 \
    httpx>=0.27.0 \
    prometheus-client>=0.21.0

# Copy source code
COPY src/ ./src/

# Change ownership to non-root user
RUN chown -R appuser:appgroup /app

# Switch to non-root user before runtime
USER appuser

# Expose port
EXPOSE 8006

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8006/health || exit 1

# Run the application
CMD ["python", "-m", "uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8006"]
