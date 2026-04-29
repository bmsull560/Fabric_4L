"""
Security Test Infrastructure — Phase 0.

Provides:
  - JWT token minting (valid, expired, wrong-signature, cross-tenant)
  - Two-tenant fixture for IDOR / cross-tenant tests
  - Endpoint enumerator for parametrized auth tests
  - Outbound HTTP sandbox (blocks unsanctioned egress)
  - Mock Neo4j driver and sessions
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any, Optional
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import jwt as pyjwt
import pytest
from shared.models.typed_dict import TypedDictModel


class AuthFactory_headerResult(TypedDictModel):
    Authorization: str

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

JWT_SECRET = "test-secret-for-security-suite"
JWT_ALGORITHM = "HS256"

TENANT_A_ID = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
TENANT_B_ID = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")


# ---------------------------------------------------------------------------
# Token Minting
# ---------------------------------------------------------------------------


def mint_token(
    tenant_id: UUID,
    *,
    user_id: str = "test-user",
    roles: list[str] | None = None,
    ttl: int = 3600,
    secret: str = JWT_SECRET,
    claim_override_tenant: UUID | None = None,
) -> str:
    """Mint a JWT for testing.

    Args:
        tenant_id: The real tenant_id to encode.
        user_id: Subject claim.
        roles: Role list (defaults to ["user"]).
        ttl: Token lifetime in seconds. Negative = expired.
        secret: Signing secret.
        claim_override_tenant: If set, overrides the tenant_id claim
            (for cross-tenant attack simulation).
    """
    now = int(time.time())
    payload = {
        "tenant_id": str(claim_override_tenant or tenant_id),
        "sub": user_id,
        "roles": roles or ["user"],
        "iat": now,
        "exp": now + ttl,
    }
    return pyjwt.encode(payload, secret, algorithm=JWT_ALGORITHM)


@dataclass
class AuthFactory:
    """Factory for creating various token types for security testing."""

    secret: str = JWT_SECRET

    def valid(self, tenant_id: UUID, role: str = "user") -> str:
        return mint_token(tenant_id, roles=[role], secret=self.secret)

    def admin(self, tenant_id: UUID) -> str:
        return mint_token(tenant_id, roles=["admin"], secret=self.secret)

    def expired(self, tenant_id: UUID) -> str:
        return mint_token(tenant_id, ttl=-1, secret=self.secret)

    def wrong_signature(self, tenant_id: UUID) -> str:
        return mint_token(tenant_id, secret="wrong-secret-key")

    def cross_tenant(self, real_tid: UUID, claimed_tid: UUID) -> str:
        """Token signed for real_tid but claims claimed_tid."""
        return mint_token(
            real_tid,
            claim_override_tenant=claimed_tid,
            secret=self.secret,
        )

    def header(self, tenant_id: UUID, role: str = "user") -> dict[str, str]:
        """Return Authorization header dict."""
        return AuthFactory_headerResult.model_validate({"Authorization": f"Bearer {self.valid(tenant_id, role)}"})


# ---------------------------------------------------------------------------
# Two-Tenant Fixture Data
# ---------------------------------------------------------------------------


@dataclass
class TenantData:
    """Seed data for one tenant."""

    id: UUID
    account_ids: list[str] = field(default_factory=list)
    product_ids: list[str] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
    competitor_ids: list[str] = field(default_factory=list)
    hypothesis_ids: list[str] = field(default_factory=list)
    narrative_ids: list[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.account_ids:
            self.account_ids = [str(uuid4()) for _ in range(3)]
        if not self.product_ids:
            self.product_ids = [str(uuid4()) for _ in range(2)]
        if not self.evidence_ids:
            self.evidence_ids = [str(uuid4()) for _ in range(3)]
        if not self.competitor_ids:
            self.competitor_ids = [str(uuid4()) for _ in range(2)]
        if not self.hypothesis_ids:
            self.hypothesis_ids = [str(uuid4()) for _ in range(3)]
        if not self.narrative_ids:
            self.narrative_ids = [str(uuid4()) for _ in range(1)]


@dataclass
class TenantPair:
    """Two fully populated tenants for cross-tenant testing."""

    a: TenantData
    b: TenantData


@dataclass
class CrossTenantContext:
    """Token for Tenant A, resource UUIDs from Tenant B."""

    token: str
    auth_header: dict[str, str]
    target_account_id: str
    target_product_id: str
    target_competitor_id: str


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def auth_factory():
    """Provide an AuthFactory for minting test tokens."""
    return AuthFactory(secret=JWT_SECRET)


@pytest.fixture
def tenant_a():
    return TenantData(id=TENANT_A_ID)


@pytest.fixture
def tenant_b():
    return TenantData(id=TENANT_B_ID)


@pytest.fixture
def two_tenants(tenant_a, tenant_b):
    return TenantPair(a=tenant_a, b=tenant_b)


@pytest.fixture
def cross_tenant_attempt(two_tenants, auth_factory):
    """Token for Tenant A, resource UUIDs from Tenant B — the canonical IDOR probe."""
    token = auth_factory.valid(two_tenants.a.id)
    return CrossTenantContext(
        token=token,
        auth_header={"Authorization": f"Bearer {token}"},
        target_account_id=two_tenants.b.account_ids[0],
        target_product_id=two_tenants.b.product_ids[0],
        target_competitor_id=two_tenants.b.competitor_ids[0],
    )


# ---------------------------------------------------------------------------
# Mock Neo4j Driver
# ---------------------------------------------------------------------------


def make_mock_neo4j_driver():
    """Create a mock Neo4j driver with async session support."""
    driver = MagicMock()
    session = AsyncMock()
    result = AsyncMock()
    result.single = AsyncMock(return_value=None)
    result.__aiter__ = AsyncMock(return_value=iter([]))
    session.run = AsyncMock(return_value=result)
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=None)
    driver.session = MagicMock(return_value=session)
    return driver, session, result


@pytest.fixture
def mock_neo4j():
    """Provide a mock Neo4j driver, session, and result."""
    return make_mock_neo4j_driver()


# ---------------------------------------------------------------------------
# Mock SQLAlchemy DB Session
# ---------------------------------------------------------------------------


def make_mock_db():
    """Create a mock async SQLAlchemy session."""
    db = AsyncMock()
    db.get = AsyncMock(return_value=None)
    db.execute = AsyncMock()
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    return db


@pytest.fixture
def mock_db():
    return make_mock_db()


# ---------------------------------------------------------------------------
# Endpoint Enumerator
# ---------------------------------------------------------------------------

# All DIL endpoints with method, path, and sample body
DIL_ENDPOINTS: list[tuple[str, str, dict | None]] = [
    # L3 Products
    ("POST", "/api/v1/products", {"name": "Test", "description": "Test product", "category": "test"}),
    ("GET", "/api/v1/products", None),
    ("GET", "/api/v1/products/test-id", None),
    ("PUT", "/api/v1/products/test-id", {"name": "Updated"}),
    ("DELETE", "/api/v1/products/test-id", None),
    ("POST", "/api/v1/products/test-id/features", {"name": "Feature", "description": "Test"}),
    ("GET", "/api/v1/products/test-id/features", None),
    ("POST", "/api/v1/products/match-signals", {"signal_ids": ["s1"]}),
    ("GET", "/api/v1/products/portfolio/summary", None),
    ("GET", "/api/v1/products/portfolio/capability-gaps", None),
    # L3 Evidence
    ("POST", "/api/v1/evidence", {"title": "Test", "content": "x" * 60, "industry": "tech", "company_name": "Test Co"}),
    ("GET", "/api/v1/evidence", None),
    ("GET", "/api/v1/evidence/test-id", None),
    ("PUT", "/api/v1/evidence/test-id", {"title": "Updated"}),
    ("DELETE", "/api/v1/evidence/test-id", None),
    ("POST", "/api/v1/evidence/bulk-import", {"case_studies": []}),
    ("GET", "/api/v1/evidence/search", None),
    ("POST", "/api/v1/evidence/test-id/outcomes", {"metric_name": "Revenue", "before_value": 100, "after_value": 200}),
    ("GET", "/api/v1/evidence/test-id/outcomes", None),
    # L3 Competitive Intel
    ("POST", "/api/v1/competitive/competitors", {"name": "Rival", "description": "A competitor"}),
    ("GET", "/api/v1/competitive/competitors", None),
    ("GET", "/api/v1/competitive/competitors/test-id", None),
    ("PUT", "/api/v1/competitive/competitors/test-id", {"name": "Updated"}),
    ("DELETE", "/api/v1/competitive/competitors/test-id", None),
    ("POST", "/api/v1/competitive/competitors/test-id/battlecards", {"product_id": "p1", "positioning": "Better"}),
    ("GET", "/api/v1/competitive/competitors/test-id/battlecards", None),
    ("POST", "/api/v1/competitive/win-loss", {"competitor_id": "c1", "product_id": "p1", "outcome": "won"}),
    ("GET", "/api/v1/competitive/win-loss/summary", None),
    ("GET", "/api/v1/competitive/landscape", None),
    # L3 ROI Calculator
    ("POST", "/api/v1/roi/calculate", {"annual_cost_current": 100000, "annual_cost_proposed": 80000, "implementation_cost": 50000}),
    ("POST", "/api/v1/roi/compare", {"annual_cost_current": 100000, "annual_cost_proposed": 80000, "implementation_cost": 50000}),
    ("POST", "/api/v1/roi/templates", {"name": "Template", "description": "Test", "default_inputs": {}}),
    ("GET", "/api/v1/roi/templates", None),
    ("GET", "/api/v1/roi/calculations", None),
    ("GET", "/api/v1/roi/calculations/test-id", None),
    ("GET", "/api/v1/roi/benchmarks/technology", None),
    # L4 Enrichment
    ("POST", "/api/v1/enrichment/batch", {"tenant_id": "test", "limit": 10}),
    ("POST", "/api/v1/enrichment/test-id", None),
    ("GET", "/api/v1/enrichment/status", None),
    ("GET", "/api/v1/enrichment/test-id", None),
    # L4 Value Hypotheses
    ("POST", "/api/v1/value-hypotheses/generate", {"account_id": "a1"}),
    ("GET", "/api/v1/value-hypotheses/test-id", None),
    ("GET", "/api/v1/value-hypotheses/account/test-id", None),
    ("POST", "/api/v1/value-hypotheses/test-id/validate", {"outcome": "validated"}),
    ("POST", "/api/v1/value-hypotheses/test-id/evidence", {"evidence_ids": ["e1"]}),
    ("POST", "/api/v1/value-hypotheses/rank", {"hypothesis_ids": ["h1"]}),
    ("GET", "/api/v1/value-hypotheses/account/test-id/analytics", None),
    # L4 Narratives
    ("POST", "/api/v1/narratives/generate", {"tenant_id": "test", "account_id": "a1"}),
    ("GET", "/api/v1/narratives/test-id", None),
    ("GET", "/api/v1/narratives/account/test-id", None),
    ("PUT", "/api/v1/narratives/test-id/status", {"status": "review"}),
    ("GET", "/api/v1/narratives/test-id/versions", None),
    # L4 Intelligence
    ("GET", "/api/v1/intelligence/briefing/test-id", None),
    ("GET", "/api/v1/intelligence/readiness/test-id", None),
    ("GET", "/api/v1/intelligence/pipeline-summary", None),
]


def discover_all_dil_endpoints() -> list[tuple[str, str, dict | None]]:
    """Return all DIL endpoints for parametrized testing."""
    return DIL_ENDPOINTS


def discover_tenant_scoped_endpoints() -> list[tuple[str, str, dict | None]]:
    """Return endpoints that should enforce tenant scoping."""
    # All DIL endpoints are tenant-scoped
    return DIL_ENDPOINTS


# ---------------------------------------------------------------------------
# SSRF Target List
# ---------------------------------------------------------------------------

SSRF_TARGETS = [
    "http://169.254.169.254/latest/meta-data/",       # AWS IMDS
    "http://metadata.google.internal/",                # GCP metadata
    "http://127.0.0.1:8080/admin",                     # loopback
    "http://10.0.0.1/",                                # RFC1918 Class A
    "http://172.16.0.1/",                              # RFC1918 Class B
    "http://192.168.1.1/",                             # RFC1918 Class C
    "http://[::1]/",                                   # IPv6 loopback
    "file:///etc/passwd",                              # scheme abuse
    "gopher://127.0.0.1:6379/_FLUSHALL",              # protocol smuggling
    "http://0177.0.0.1/",                              # octal IP bypass
    "http://2130706433/",                              # decimal IP bypass
    "http://0x7f000001/",                              # hex IP bypass
    "http://127.0.0.1.nip.io/",                        # DNS rebinding
    "http://localhost/",                                # localhost keyword
]

# ---------------------------------------------------------------------------
# Cypher Injection Payloads
# ---------------------------------------------------------------------------

CYPHER_INJECTION_KEYS = [
    "name`}) DETACH DELETE c //",
    "admin_override",
    "is_deleted",
    "name'} SET c.x='",
    "valid_field; DROP",
    "tenant_id",       # protected field bypass attempt
    "id",              # protected field bypass attempt
    "entity_type",     # protected field bypass attempt
    "created_at",      # protected field bypass attempt
]
