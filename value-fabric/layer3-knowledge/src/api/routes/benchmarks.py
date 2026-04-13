"""Benchmark API routes for Layer 3.

Provides endpoints for benchmark CRUD and policy management.
Benchmarks are stored as Neo4j Benchmark nodes and may be linked to
ValuePacks via hasBenchmark relationships.
"""

from typing import List, Optional, Dict, Any, Literal
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from ...db.driver import get_driver
from neo4j import AsyncDriver
from ...logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter()


# ── Pydantic Models ──────────────────────────────────────────────────────────

class BenchmarkSummary(BaseModel):
    """Benchmark list item."""
    id: str
    benchmark_id: str
    name: str
    industry: str
    vertical: Optional[str] = None
    value_range: str
    confidence: Literal["High", "Medium", "Low"]
    source: str
    source_url: Optional[str] = None
    year: int
    status: Literal["active", "draft", "deprecated"]
    tags: List[str] = Field(default_factory=list)
    last_verified: Optional[str] = None
    usage_count: int = 0
    description: Optional[str] = None


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
    name: Optional[str] = None
    description: Optional[str] = None
    value: Optional[str] = None
    is_enabled: Optional[bool] = None
    scope: Optional[Literal["tenant", "pack", "formula"]] = None


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/benchmarks", response_model=List[BenchmarkSummary])
async def list_benchmarks(
    industry: Optional[str] = Query(None, description="Filter by industry"),
    status: Optional[str] = Query(None, description="Filter by status"),
    confidence: Optional[str] = Query(None, description="Filter by confidence level"),
    search: Optional[str] = Query(None, description="Search benchmarks by name"),
    driver: AsyncDriver = Depends(get_driver),
):
    """List benchmarks with optional filters."""
    where_conditions: List[str] = []
    params: Dict[str, Any] = {}

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
    """

    async with driver.session() as session:
        result = await session.run(query, **params)
        records = await result.data()

        current_year = datetime.now(timezone.utc).year
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
                tags=r["b"].get("tags", []) if isinstance(r["b"].get("tags"), list) else [],
                last_verified=r["b"].get("lastVerified"),
                usage_count=r.get("usage_count", 0),
                description=r["b"].get("description"),
            )
            for r in records
        ]


@router.get("/benchmarks/policies", response_model=List[BenchmarkPolicy])
async def list_benchmark_policies(
    driver: AsyncDriver = Depends(get_driver),
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
    benchmark_id: str,
    driver: AsyncDriver = Depends(get_driver),
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
        current_year = datetime.now(timezone.utc).year
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
    policy_id: str,
    update: BenchmarkPolicyUpdate,
    driver: AsyncDriver = Depends(get_driver),
):
    """Update a benchmark policy."""
    # Build SET clauses dynamically from provided fields
    set_parts: List[str] = []
    params: Dict[str, Any] = {"policy_id": policy_id}

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

    now = datetime.now(timezone.utc).isoformat()
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
