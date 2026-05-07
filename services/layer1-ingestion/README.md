# Layer 1: Intelligent Data Ingestion Service
> Routing/versioning reference: see the canonical [Service Routing and API Version Matrix](../../docs/reference/service-routing-and-api-version-matrix.md).

A production-grade web data ingestion service that continuously acquires unstructured enterprise data from public sources and converts it to clean, structured Markdown ready for semantic processing by Layer 2.

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)

### Running with Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f api
docker-compose logs -f worker

# Initialize database (first time only)
docker-compose exec api alembic upgrade head
```

### Local Development Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Set environment variables
export LAYER1_DATABASE_URL="postgresql://postgres:postgres@localhost:5432/layer1_ingestion"
export LAYER1_REDIS_URL="redis://localhost:6379/0"

# Run database migrations
alembic upgrade head

# Start API server
uvicorn src.api.main:app --reload --port 8000

# Start Celery worker (in another terminal)
celery -A src.shared.tasks worker --loglevel=info
```

## Architecture

### Services

- **API** (`src/api/main.py`): FastAPI REST endpoints
- **Crawler** (`src/crawler/`): Playwright-based web crawling
- **Post-Processor** (`src/post_processor/`): Content extraction and Markdown conversion
- **Scheduler**: Priority-based job scheduling via Celery

### Data Flow

```
1. API receives crawl request
   ↓
2. Job created in PostgreSQL, URL added to queue
   ↓
3. Celery worker picks up task
   ↓
4. Playwright crawls URL, renders JS
   ↓
5. Content extracted and converted to Markdown
   ↓
6. Results stored in PostgreSQL, raw HTML in MinIO/S3
   ↓
7. Ready for Layer 2 extraction
```

## API Endpoints

### Crawl Operations

- `POST /v1/crawl/website` - Start website crawl
- `POST /v1/crawl/sec-filings` - Fetch SEC EDGAR filings
- `GET /v1/crawl/status/{job_id}` - Check crawl status

### Content Management

- `GET /v1/content` - List crawled content
- `GET /v1/content/{content_id}` - Get specific content
- `DELETE /v1/content/{content_id}` - Soft-delete content

### Job Management

- `GET /v1/jobs` - List crawl jobs

### Admin

- `POST /v1/admin/cleanup` - Trigger old content cleanup

## Configuration

Environment variables (all prefixed with `LAYER1_`):

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql://postgres:postgres@localhost:5432/layer1_ingestion` | PostgreSQL connection |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection |
| `S3_ENDPOINT` | `http://localhost:9000` | MinIO/S3 endpoint |
| `API_PORT` | `8000` | API server port |
| `MAX_CONCURRENT_PAGES` | `5` | Max concurrent crawls |

## Testing

```bash
# Run unit tests
pytest tests/unit -v

# Run integration tests
pytest tests/integration -v

# Run with coverage
pytest --cov=src --cov-report=html
```

## Project Structure

```
layer1-ingestion/
├── src/
│   ├── api/
│   │   └── main.py           # FastAPI application
│   ├── crawler/
│   │   ├── playwright_crawler.py
│   │   └── adapters/         # Data source adapters (SEC, patents, etc.)
│   ├── post_processor/
│   │   └── content_extractor.py
│   ├── scheduler/
│   │   └── priority_queue.py
│   └── shared/
│       ├── models.py         # SQLAlchemy models
│       ├── config.py         # Configuration
│       ├── database.py       # DB connection
│       └── tasks.py          # Celery tasks
├── migrations/               # Alembic migrations
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

## License

Internal Value Fabric Project
