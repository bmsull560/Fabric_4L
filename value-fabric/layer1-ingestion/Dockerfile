# Multi-stage build for Layer 1: Data Ingestion Service
# Stage 1: Builder - installs dependencies and Playwright browsers
FROM python:3.11.11-slim-bookworm AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies to system site-packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN python -m playwright install chromium
RUN python -m playwright install-deps chromium

# Stage 2: Runtime - minimal image with only runtime dependencies
FROM python:3.11.11-slim-bookworm AS runtime

# Install runtime dependencies (Playwright libs + curl for healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libcairo2 \
    libatspi2.0-0 \
    poppler-utils \
    tesseract-ocr \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user with home directory
RUN groupadd -r appgroup && useradd -r -g appgroup -m appuser

WORKDIR /app

# Copy Python packages from builder (system site-packages)
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
ENV PATH=/usr/local/bin:$PATH
ENV PYTHONPATH=/usr/local/lib/python3.11/site-packages:/app/src

# Copy Playwright browsers from builder
COPY --from=builder /root/.cache/ms-playwright /home/appuser/.cache/ms-playwright
ENV PLAYWRIGHT_BROWSERS_PATH=/home/appuser/.cache/ms-playwright

# Copy application code
COPY src/ ./src/
COPY alembic.ini .
COPY migrations/ ./migrations/

# Change ownership
RUN chown -R appuser:appgroup /app /home/appuser

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Default command
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
