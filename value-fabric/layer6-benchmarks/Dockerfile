FROM python:3.11-slim

WORKDIR /app

# Install curl for healthcheck
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy dependency file
COPY pyproject.toml ./

# Install dependencies
RUN pip install --no-cache-dir fastapi uvicorn pydantic httpx

# Copy source code
COPY src/ ./src/

# Expose port
EXPOSE 8006

# Run the application
CMD ["python", "-m", "uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8006"]
