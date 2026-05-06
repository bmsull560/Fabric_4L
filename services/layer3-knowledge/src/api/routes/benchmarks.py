"""Benchmark API routes for Layer 3.

Provides endpoints for benchmark CRUD and policy management.
Benchmarks are stored as Neo4j Benchmark nodes and may be linked to
ValuePacks via hasBenchmark relationships.

SECURITY WARNING: This module is NOT tenant-scoped. Cypher queries operate
on the full graph without tenant_id filtering. This is a known gap tracked
in config/production-readiness/l3-tenant-isolation-gate.yaml.
Do NOT mark L3 tenant isolation complete until this module is migrated.
See: docs/audit/l3-neo4j-label-tenant-classification.md (T1)
"""

from datetime import UTC, datetime
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from neo4j import AsyncDriver
from pydantic import BaseModel, Field

from ...auth.api_keys import APIKey
from ...auth.middleware import get_current_api_key
from ...db.driver import get_driver
from ...logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter()

# Pagination limits
MAX_PAGE_SIZE = 100
DEFAULT_PAGE_SIZE = 50


# ── Pydantic Models ──────────────────────────────────────────────────────────


class BenchmarkSummary(BaseModel):
    """Benchmark list item."""

    id: str
    benchmark_id: str
    name: str
    industry: str
    vertical: str | None = None
    value_range: str
    confidence: Literal["High", "Medium", "Low"]
    source: str
    source_url: str | None = None
    year: int
    status: Literal["active", "draft", "deprecated"]
    tags: list[str] = Field(default_factory=list)
    last_verified: str | None = None
    usage_count: int = 0
    description: str | None = None


class BenchmarkPolicy(BaseModel):
    """Benchmark policy configuration."""

    id: str
    policy_type: Literal["threshold", "cadence", "fallback", "override"]
    name: str
    description: str
    value: str
    is_enabled: bool = True
    scope: Literal["tenant", "pack", "formula"]


class BenchmarkPolicyUpdate(BaseModel):
    """Update payload for a benchmark policy (all fields optional)."""

    name: str | None = None
    description: str | None = None
    value: str | None = None
    is_enabled: bool | None = None
    scope: Literal["tenant", "pack", "formula"] | None = None


# ── Endpoints ────────────────────────────────────────────────────────────────


@router.get("/benchmarks", response_model=list[BenchmarkSummary])
async def list_benchmarks(
    # SECURITY-TODO: Cypher queries in this handler are not tenant-scoped.
    # See module docstring and l3-tenant-isolation-gate.yaml.
    industry: str | None = Query(None, description="Filter by industry"),
    status: str | None = Query(None, description="Filter by status"),
    confidence: str | None = Query(None, description="Filter by confidence level"),
    search: str | None = Query(None, description="Search benchmarks by name"),
    limit: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE, description="Maximum results to return"),
    driver: AsyncDriver = Depends(get_driver),
    api_key: APIKey = Depends(get_current_api_key),
):
    """List benchmarks with optional filters."""
    where_conditions: list[str] = []
    params: dict[str, Any] = {"limit": limit}

    if industry:
        where_conditions.append("b.industry = $industry")
        params["industry"] = industry

    if status:
        where_conditions.append("b.status = $status")
        params["status"] = status

    if confidence:
        where_conditions.append("b.confidence = $confidence")
        params["confidence"] = confidence

    if search:
        where_conditions.append("toLower(b.name) CONTAINS toLower($search)")
        params["search"] = search

    where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""

    query = f"""
    MATCH (b:Benchmark)
    {where_clause}
    OPTIONAL MATCH (vp:ValuePack)-[:hasBenchmark]->(b)
    RETURN b, count(DISTINCT vp) as usage_count
    ORDER BY b.name
    LIMIT $limit
    """

    async with driver.session() as session:
        result = await session.run(query, **params)
        records = await result.data()

        current_year = datetime.now(UTC).year
        return [
            BenchmarkSummary(
                id=r["b"]["id"],
                benchmark_id=r["b"].get("benchmarkId", r["b"]["id"]),
                name=r["b"]["name"],
                industry=r["b"].get("industry", "General"),
                vertical=r["b"].get("vertical"),
                value_range=r["b"].get("valueRange", ""),
                confidence=r["b"].get("confidence", "Medium"),
                source=r["b"].get("source", ""),
                source_url=r["b"].get("sourceUrl"),
                year=r["b"].get("year", current_year),
                status=r["b"].get("status", "active"),
                tags=r["b"].get("tags", [])
                if isinstance(r["b"].get("tags"), list)
                else [],
                last_verified=r["b"].get("lastVerified"),
                usage_count=r.get("usage_count", 0),
                description=r["b"].get("description"),
            )
            for r in records
        ]


@router.get("/benchmarks/policies", response_model=list[BenchmarkPolicy])
async def list_benchmark_policies(
    # SECURITY-TODO: Cypher queries in this handler are not tenant-scoped.
    # See module docstring and l3-tenant-isolation-gate.yaml.
    driver: AsyncDriver = Depends(get_driver),
    api_key: APIKey = Depends(get_current_api_key),
):
    """List benchmark policy configurations."""
    query = """
    MATCH (bp:BenchmarkPolicy)
    RETURN bp
    ORDER BY bp.name
    """

    async with driver.session() as session:
        result = await session.run(query)
        records = await result.data()

        return [
            BenchmarkPolicy(
                id=r["bp"]["id"],
                policy_type=r["bp"]["policyType"],
                name=r["bp"]["name"],
                description=r["bp"].get("description", ""),
                value=r["bp"].get("value", ""),
                is_enabled=r["bp"].get("isEnabled", True),
                scope=r["bp"].get("scope", "tenant"),
            )
            for r in records
        ]


@router.get("/benchmarks/{benchmark_id}", response_model=BenchmarkSummary)
async def get_benchmark(
    # SECURITY-TODO: Cypher queries in this handler are not tenant-scoped.
    # See module docstring and l3-tenant-isolation-gate.yaml.
    benchmark_id: str,
    driver: AsyncDriver = Depends(get_driver),
    api_key: APIKey = Depends(get_current_api_key),
):
    """Get a single benchmark by ID."""
    query = """
    MATCH (b:Benchmark {id: $benchmark_id})
    OPTIONAL MATCH (vp:ValuePack)-[:hasBenchmark]->(b)
    RETURN b, count(DISTINCT vp) as usage_count
    """

    async with driver.session() as session:
        result = await session.run(query, benchmark_id=benchmark_id)
        record = await result.single()

        if not record:
            raise HTTPException(status_code=404, detail="Benchmark not found")

        b = record["b"]
        current_year = datetime.now(UTC).year
        return BenchmarkSummary(
            id=b["id"],
            benchmark_id=b.get("benchmarkId", b["id"]),
            name=b["name"],
            industry=b.get("industry", "General"),
            vertical=b.get("vertical"),
            value_range=b.get("valueRange", ""),
            confidence=b.get("confidence", "Medium"),
            source=b.get("source", ""),
            source_url=b.get("sourceUrl"),
            year=b.get("year", current_year),
            status=b.get("status", "active"),
            tags=b.get("tags", []) if isinstance(b.get("tags"), list) else [],
            last_verified=b.get("lastVerified"),
            usage_count=record.get("usage_count", 0),
            description=b.get("description"),
        )


@router.put("/benchmarks/policies/{policy_id}", response_model=BenchmarkPolicy)
async def update_benchmark_policy(
    # SECURITY-TODO: Cypher queries in this handler are not tenant-scoped.
    # See module docstring and l3-tenant-isolation-gate.yaml.
    policy_id: str,
    update: BenchmarkPolicyUpdate,
    driver: AsyncDriver = Depends(get_driver),
    api_key: APIKey = Depends(get_current_api_key),
):
    """Update a benchmark policy."""
    # Build SET clauses dynamically from provided fields
    set_parts: list[str] = []
    params: dict[str, Any] = {"policy_id": policy_id}

    update_data = update.model_dump(exclude_none=True)
    field_map = {
        "name": "name",
        "description": "description",
        "value": "value",
        "is_enabled": "isEnabled",
        "scope": "scope",
    }

    for py_field, neo_field in field_map.items():
        if py_field in update_data:
            set_parts.append(f"bp.{neo_field} = ${py_field}")
            params[py_field] = update_data[py_field]

    if not set_parts:
        raise HTTPException(status_code=400, detail="No fields to update")

    now = datetime.now(UTC).isoformat()
    set_parts.append("bp.updatedAt = $updated_at")
    params["updated_at"] = now

    set_clause = ", ".join(set_parts)

    query = f"""
    MATCH (bp:BenchmarkPolicy {{id: $policy_id}})
    SET {set_clause}
    RETURN bp
    """

    async with driver.session() as session:
        result = await session.run(query, **params)
        record = await result.single()

        if not record:
            raise HTTPException(status_code=404, detail="Policy not found")

        bp = record["bp"]
        return BenchmarkPolicy(
            id=bp["id"],
            policy_type=bp["policyType"],
            name=bp["name"],
            description=bp.get("description", ""),
            value=bp.get("value", ""),
            is_enabled=bp.get("isEnabled", True),
            scope=bp.get("scope", "tenant"),
        )
