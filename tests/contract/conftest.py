"""
Shared fixtures for contract tests.

Environment Variables:
    LAYER3_API_URL: Layer 3 Knowledge API base URL (default: http://localhost:8003)
    LAYER5_API_URL: Layer 5 Ground Truth API base URL (default: http://localhost:8005)
    CONTRACT_TEST_TIMEOUT: Request timeout in seconds (default: 10.0)
    CONTRACT_TEST_MODE: Set to 'mock' to use mocked fixtures (see conftest_mocked.py)

Note:
    For CI environments without running services, use conftest_mocked.py which provides
    respx-based mocked fixtures. Install test dependencies: pip install -r tests/requirements.txt
"""

import os
import urllib.request
import urllib.error

import pytest
from httpx import AsyncClient

# Default API endpoints for local development
DEFAULT_LAYER3_URL = "http://localhost:8003"
DEFAULT_LAYER4_URL = "http://localhost:8004"
DEFAULT_LAYER5_URL = "http://localhost:8005"
DEFAULT_TIMEOUT = 10.0


def _get_env_url(env_var: str, default: str) -> str:
    """Get API URL from environment variable with fallback to default.

    Strips trailing slashes to ensure consistent URL construction.
    """
    url = os.getenv(env_var, default)
    return url.rstrip("/")

@pytest.fixture(scope="session", autouse=True)
def check_services_availability():
    """Check if required services are running, otherwise skip tests.
    Prevents massive traceback dumps when backend infrastructure is missing.
    """
    if os.getenv("CONTRACT_TEST_MODE") == "mock":
        return

    # We only check health endpoints if this is an environment where we expect real APIs.
    urls_to_check = [
        f"{_get_env_url('LAYER3_API_URL', DEFAULT_LAYER3_URL)}/health",
        f"{_get_env_url('LAYER4_API_URL', DEFAULT_LAYER4_URL)}/health",
        f"{_get_env_url('LAYER5_API_URL', DEFAULT_LAYER5_URL)}/api/v1/health"
    ]

    missing_services = []
    for url in urls_to_check:
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=2) as response:
                if response.status != 200:
                    missing_services.append(url)
        except (urllib.error.URLError, ConnectionError):
            missing_services.append(url)

    if missing_services:
        if os.getenv("CONTRACT_TEST_STRICT") == "1":
            pytest.fail(f"CONTRACT_TEST_STRICT=1 but required services are unavailable. Missing: {missing_services}")
        else:
            pytest.skip(f"Required contract services are unavailable. Skipping tests instead of failing. Missing: {missing_services}")


@pytest.fixture
async def client() -> AsyncClient:
    """Create HTTP client for Layer 3 API contract tests.

    Uses LAYER3_API_URL environment variable, falls back to localhost:8003.
    """
    base_url = _get_env_url("LAYER3_API_URL", DEFAULT_LAYER3_URL)
    timeout = float(os.getenv("CONTRACT_TEST_TIMEOUT", DEFAULT_TIMEOUT))

    async with AsyncClient(base_url=base_url, timeout=timeout) as client:
        yield client


@pytest.fixture
async def layer4_client() -> AsyncClient:
    """Create HTTP client for Layer 4 Agents API tests.

    Uses LAYER4_API_URL environment variable, falls back to localhost:8004.
    """
    base_url = _get_env_url("LAYER4_API_URL", DEFAULT_LAYER4_URL)
    timeout = float(os.getenv("CONTRACT_TEST_TIMEOUT", DEFAULT_TIMEOUT))

    async with AsyncClient(base_url=base_url, timeout=timeout) as client:
        yield client


@pytest.fixture
async def layer5_client() -> AsyncClient:
    """Create HTTP client for Layer 5 Ground Truth API tests.

    Uses LAYER5_API_URL environment variable, falls back to localhost:8005.
    """
    base_url = _get_env_url("LAYER5_API_URL", DEFAULT_LAYER5_URL)
    timeout = float(os.getenv("CONTRACT_TEST_TIMEOUT", DEFAULT_TIMEOUT))

    async with AsyncClient(base_url=base_url, timeout=timeout) as client:
        yield client
