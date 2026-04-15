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

# Install Python dependencies from lockfile
COPY requirements.lock .
RUN pip install --no-cache-dir -r requirements.lock

# Copy application code
COPY src/ ./src/

# Change ownership to non-root user
RUN chown -R appuser:appgroup /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
