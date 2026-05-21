# syntax=docker/dockerfile:1
ARG BUILDER_BASE_IMAGE=ghcr.io/value-fabric/ci-mirror/astral-uv:python3.11-bookworm-slim@sha256:7b96c4cb5e0d3fa2be3d3f1ee3ab6e3a9ec8f0c443b2d0d94fcf4d972cb9e431
FROM ${BUILDER_BASE_IMAGE} AS builder
WORKDIR /app
ENV UV_TORCH_BACKEND=cpu
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

ARG BASE_IMAGE=ghcr.io/value-fabric/base-images/python:3.11.13-slim-bookworm@sha256:86adf8dbadc3d6e82ee5dd2c74bec2e1c2467cdad47886280501df722372d2e1
FROM ${BASE_IMAGE}
WORKDIR /app
RUN apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
COPY --from=builder /app/.venv /app/.venv
COPY --from=ghcr.io/astral-sh/uv:0.11.6 /uv /uvx /bin/
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH=/app \
    UVICORN_CMD="uvicorn value_fabric.layer3.api.main:app --host 0.0.0.0 --port 8001"
COPY src/ ./src/
RUN groupadd -r appgroup && useradd -r -g appgroup -m appuser
USER appuser
EXPOSE 8001
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1
CMD ["uvicorn", "value_fabric.layer3.api.main:app", "--host", "0.0.0.0", "--port", "8001"]
