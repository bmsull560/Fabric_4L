FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS builder
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

FROM python:3.11-slim-bookworm
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH=/app \
    UVICORN_CMD="uvicorn src.api.main:app --host 0.0.0.0 --port 8001"
COPY src/ ./value_fabric/layer3/
RUN groupadd -r appgroup && useradd -r -g appgroup appuser
USER appuser
EXPOSE 8001
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 CMD curl -f http://localhost:8001/health || exit 1
CMD ["uvicorn", "value_fabric.layer3.api.main:app", "--host", "0.0.0.0", "--port", "8001"]
