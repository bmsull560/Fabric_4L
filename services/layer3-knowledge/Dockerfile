# syntax=docker/dockerfile:1
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS builder
WORKDIR /app
ENV UV_TORCH_BACKEND=cpu
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

FROM python:3.11-slim-bookworm@sha256:081075da77b2b55c23c088251026fb69a7b2bf92471e491ff5fd75c192fd38e5
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
COPY --from=builder /app/.venv /app/.venv
COPY --from=ghcr.io/astral-sh/uv:0.11.6 /uv /uvx /bin/
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH=/app \
    UVICORN_CMD="uvicorn src.api.main:app --host 0.0.0.0 --port 8001"
COPY src/ ./src/
COPY value_fabric/ ./value_fabric/
RUN groupadd -r appgroup && useradd -r -g appgroup -m appuser
USER appuser
EXPOSE 8001
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8001"]
