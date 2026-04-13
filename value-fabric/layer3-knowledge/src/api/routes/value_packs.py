"""Value Pack API routes for Layer 3.

Provides endpoints for Value Pack CRUD and execution.
"""

from datetime import UTC, datetime
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from neo4j import AsyncDriver
from pydantic import BaseModel, Field

from ...db.driver import get_driver
from ...logging_config import get_logger
from ._utils import increment_patch_version

logger = get_logger(__name__)

# Status constants for Value Packs
STATUS_DRAFT = "draft"
STATUS_PUBLISHED = "published"
STATUS_DEPRECATED = "deprecated"
STATUS_ARCHIVED = "archived"

router = APIRouter()


# Pydantic Models


class ValueDriverSummary(BaseModel):
    """Summary of value driver in pack."""

    driver_id: str
    name: str
    category: str
    weight: float = 1.0


class FormulaSummary(BaseModel):
    """Summary of formula in pack."""

    formula_id: str
    name: str
    version: str
    variables: list[str]


class BenchmarkSummary(BaseModel):
    """Summary of benchmark in pack."""

    dataset_id: str
    metric: str
    industry: str


class PackSummary(BaseModel):
    """Summary of Value Pack."""

    pack_id: str
    name: str
    industry: str
    segment: str | None
    status: str
    version: str
    driver_count: int
    formula_count: int
    benchmark_count: int
    updated_at: str | None = None


class PackDetail(BaseModel):
    """Full Value Pack detail."""

    pack_id: str
    name: str
    description: str
    industry: str
    segment: str | None
    status: str
    version: str
    drivers: list[ValueDriverSummary]
    formulas: list[FormulaSummary]
    benchmarks: list[BenchmarkSummary]
    created_at: str
    updated_at: str | None = None
    created_by: str | None = None
    workspace_id: str | None = None
    is_loaded: bool = False


VALID_PACK_STATUSES = [
    STATUS_DRAFT,
    STATUS_PUBLISHED,
    STATUS_DEPRECATED,
    STATUS_ARCHIVED,
]


class PackCreateRequest(BaseModel):
    """Request to create a Value Pack."""

    name: str
    description: str
    industry: str
    segment: str | None = None
    status: Literal["draft", "published", "deprecated", "archived"] = STATUS_DRAFT
    driver_ids: list[str] = Field(default_factory=list)
    formula_ids: list[str] = Field(default_factory=list)
    benchmark_ids: list[str] = Field(default_factory=list)
    created_by: str | None = None


class PackUpdateRequest(BaseModel):
    """Request to update a Value Pack."""

    name: str | None = None
    description: str | None = None
    industry: str | None = None
    segment: str | None = None
    status: Literal["draft", "published", "deprecated", "archived"] | None = None
    driver_ids: list[str] | None = None
    formula_ids: list[str] | None = None
    benchmark_ids: list[str] | None = None


class PackExecuteRequest(BaseModel):
    """Request to execute a pack."""

    workspace_id: str
    variables: dict[str, Any] = Field(default_factory=dict)
    user_id: str | None = None


class PackExecuteResponse(BaseModel):
    """Response from pack execution."""

    execution_id: str
    pack_id: str
    status: str
    outputs: dict[str, Any]
    errors: list[str]
    warnings: list[str] = Field(
        default_factory=list,
        description="Warning messages about partial implementation",
    )


class PackForkRequest(BaseModel):
    """Request to fork a pack."""

    workspace_id: str
    name: str | None = None
    modifications: dict[str, Any] = Field(default_factory=dict)
    user_id: str | None = None


class PackForkResponse(BaseModel):
    """Response from pack fork."""

    pack_id: str
    name: str
    version: str
    status: str


# Helper functions


async def _get_pack_detail(driver: AsyncDriver, pack_id: str) -> PackDetail | None:
    """Get full pack detail from Neo4j."""
    query = """
    MATCH (vp:ValuePack {id: $pack_id})
    OPTIONAL MATCH (vp)-[:hasDriver]->(vd:ValueDriver)
    OPTIONAL MATCH (vp)-[:hasFormula]->(f:Formula)
    OPTIONAL MATCH (vp)-[:hasBenchmark]->(b:BenchmarkDataset)
    RETURN vp,
           collect(DISTINCT vd) as drivers,
           collect(DISTINCT f) as formulas,
           collect(DISTINCT b) as benchmarks
    """

    async with driver.session() as session:
        result = await session.run(query, pack_id=pack_id)
        record = await result.single()

        if not record:
            return None

        vp = record["vp"]

        drivers = [
            ValueDriverSummary(
                driver_id=d["id"],
                name=d.get("name", ""),
                category=d.get("category", ""),
                weight=1.0,
            )
            for d in record["drivers"]
            if d
        ]

        formulas = [
            FormulaSummary(
                formula_id=f["id"],
                name=f.get("name", ""),
                version=f.get("version", "1.0.0"),
                variables=f.get("variables", []),
            )
            for f in record["formulas"]
            if f
        ]

        benchmarks = [
            BenchmarkSummary(
                dataset_id=b["id"],
                metric=b.get("metric", ""),
                industry=b.get("industry", ""),
            )
            for b in record["benchmarks"]
            if b
        ]

        return PackDetail(
            pack_id=vp["id"],
            name=vp.get("name", ""),
            description=vp.get("description", ""),
            industry=vp.get("industry", ""),
            segment=vp.get("segment"),
            status=vp.get("status", "draft"),
            version=vp.get("version", "1.0.0"),
            drivers=drivers,
            formulas=formulas,
            benchmarks=benchmarks,
            created_at=vp.get("createdAt", datetime.now(UTC).isoformat()),
            updated_at=vp.get("updatedAt"),
            created_by=vp.get("createdBy"),
            workspace_id=vp.get("workspaceId"),
            is_loaded=vp.get("isLoaded", False),
        )


# API Endpoints


@router.get("/packs", response_model=list[PackSummary])
async def list_packs(
    industry: str | None = Query(None, description="Filter by industry"),
    status: str | None = Query(None, description="Filter by status"),
    driver: AsyncDriver = Depends(get_driver),
):
    """List available Value Packs."""
    query = """
    MATCH (vp:ValuePack)
    WHERE ($industry IS NULL OR vp.industry = $industry)
      AND ($status IS NULL OR vp.status = $status)
    OPTIONAL MATCH (vp)-[:hasDriver]->(vd:ValueDriver)
    OPTIONAL MATCH (vp)-[:hasFormula]->(f:Formula)
    OPTIONAL MATCH (vp)-[:hasBenchmark]->(b:BenchmarkDataset)
    RETURN vp,
           count(DISTINCT vd) as driver_count,
           count(DISTINCT f) as formula_count,
           count(DISTINCT b) as benchmark_count
    ORDER BY vp.name
    """

    async with driver.session() as session:
        result = await session.run(
            query,
            industry=industry,
            status=status,
        )
        records = await result.data()

        return [
            PackSummary(
                pack_id=r["vp"]["id"],
                name=r["vp"].get("name", ""),
                industry=r["vp"].get("industry", ""),
                segment=r["vp"].get("segment"),
                status=r["vp"].get("status", "draft"),
                version=r["vp"].get("version", "1.0.0"),
                driver_count=r["driver_count"],
                formula_count=r["formula_count"],
                benchmark_count=r["benchmark_count"],
                updated_at=r["vp"].get("updatedAt"),
            )
            for r in records
        ]


@router.get("/packs/{pack_id}", response_model=PackDetail)
async def get_pack(
    pack_id: str,
    driver: AsyncDriver = Depends(get_driver),
):
    """Get Value Pack by ID."""
    pack = await _get_pack_detail(driver, pack_id)
    if not pack:
        raise HTTPException(status_code=404, detail="Pack not found")
    return pack


@router.post("/packs", response_model=PackDetail, status_code=201)
async def create_pack(
    request: PackCreateRequest,
    driver: AsyncDriver = Depends(get_driver),
):
    """Create a new Value Pack."""
    import uuid

    pack_id = str(uuid.uuid4())
    now = datetime.now(UTC).isoformat()

    query = """
    CREATE (vp:ValuePack {
        id: $pack_id,
        name: $name,
        description: $description,
        industry: $industry,
        segment: $segment,
        status: $status,
        version: "1.0.0",
        createdAt: $created_at,
        createdBy: $created_by
    })
    WITH vp
    OPTIONAL MATCH (vd:ValueDriver) WHERE vd.id IN $driver_ids
    FOREACH (d IN CASE WHEN vd IS NOT NULL THEN [vd] ELSE [] END |
        CREATE (vp)-[:hasDriver]->(d)
    )
    WITH vp
    OPTIONAL MATCH (f:Formula) WHERE f.id IN $formula_ids
    FOREACH (formula IN CASE WHEN f IS NOT NULL THEN [f] ELSE [] END |
        CREATE (vp)-[:hasFormula]->(formula)
    )
    WITH vp
    OPTIONAL MATCH (b:BenchmarkDataset) WHERE b.id IN $benchmark_ids
    FOREACH (benchmark IN CASE WHEN b IS NOT NULL THEN [b] ELSE [] END |
        CREATE (vp)-[:hasBenchmark]->(benchmark)
    )
    RETURN vp
    """

    async with driver.session() as session:
        await session.run(
            query,
            pack_id=pack_id,
            name=request.name,
            description=request.description,
            industry=request.industry,
            segment=request.segment,
            status=request.status,
            created_at=now,
            created_by=request.created_by,
            driver_ids=request.driver_ids,
            formula_ids=request.formula_ids,
            benchmark_ids=request.benchmark_ids,
        )

    # Return created pack
    pack = await _get_pack_detail(driver, pack_id)
    if not pack:
        raise HTTPException(status_code=500, detail="Failed to create pack")
    return pack


@router.put("/packs/{pack_id}", response_model=PackDetail)
async def update_pack(
    pack_id: str,
    request: PackUpdateRequest,
    driver: AsyncDriver = Depends(get_driver),
):
    """Update a Value Pack."""
    # Check pack exists
    check_query = "MATCH (vp:ValuePack {id: $pack_id}) RETURN vp"
    async with driver.session() as session:
        result = await session.run(check_query, pack_id=pack_id)
        if not await result.single():
            raise HTTPException(status_code=404, detail="Pack not found")

    # Build update query
    set_clauses = ["vp.updatedAt = $updated_at"]
    params = {
        "pack_id": pack_id,
        "updated_at": datetime.now(UTC).isoformat(),
    }

    if request.name is not None:
        set_clauses.append("vp.name = $name")
        params["name"] = request.name
    if request.description is not None:
        set_clauses.append("vp.description = $description")
        params["description"] = request.description
    if request.industry is not None:
        set_clauses.append("vp.industry = $industry")
        params["industry"] = request.industry
    if request.segment is not None:
        set_clauses.append("vp.segment = $segment")
        params["segment"] = request.segment
    if request.status is not None:
        set_clauses.append("vp.status = $status")
        params["status"] = request.status

    update_query = f"""
    MATCH (vp:ValuePack {{id: $pack_id}})
    SET {", ".join(set_clauses)}
    RETURN vp
    """

    async with driver.session() as session:
        await session.run(update_query, **params)

        # Update relationships if provided
        if request.driver_ids is not None:
            rel_query = """
            MATCH (vp:ValuePack {id: $pack_id})
            OPTIONAL MATCH (vp)-[r:hasDriver]->()
            DELETE r
            WITH vp
            OPTIONAL MATCH (vd:ValueDriver) WHERE vd.id IN $driver_ids
            FOREACH (d IN CASE WHEN vd IS NOT NULL THEN [vd] ELSE [] END |
                CREATE (vp)-[:hasDriver]->(d)
            )
            """
            await session.run(rel_query, pack_id=pack_id, driver_ids=request.driver_ids)

        if request.formula_ids is not None:
            rel_query = """
            MATCH (vp:ValuePack {id: $pack_id})
            OPTIONAL MATCH (vp)-[r:hasFormula]->()
            DELETE r
            WITH vp
            OPTIONAL MATCH (f:Formula) WHERE f.id IN $formula_ids
            FOREACH (formula IN CASE WHEN f IS NOT NULL THEN [f] ELSE [] END |
                CREATE (vp)-[:hasFormula]->(formula)
            )
            """
            await session.run(
                rel_query, pack_id=pack_id, formula_ids=request.formula_ids
            )

        if request.benchmark_ids is not None:
            rel_query = """
            MATCH (vp:ValuePack {id: $pack_id})
            OPTIONAL MATCH (vp)-[r:hasBenchmark]->()
            DELETE r
            WITH vp
            OPTIONAL MATCH (b:BenchmarkDataset) WHERE b.id IN $benchmark_ids
            FOREACH (benchmark IN CASE WHEN b IS NOT NULL THEN [b] ELSE [] END |
                CREATE (vp)-[:hasBenchmark]->(benchmark)
            )
            """
            await session.run(
                rel_query, pack_id=pack_id, benchmark_ids=request.benchmark_ids
            )

    pack = await _get_pack_detail(driver, pack_id)
    if not pack:
        raise HTTPException(status_code=500, detail="Failed to update pack")
    return pack


@router.post("/packs/{pack_id}/execute", response_model=PackExecuteResponse)
async def execute_pack(
    pack_id: str,
    request: PackExecuteRequest,
    driver: AsyncDriver = Depends(get_driver),
):
    """Execute a Value Pack workflow."""
    import uuid

    # Check pack exists
    check_query = "MATCH (vp:ValuePack {id: $pack_id}) RETURN vp"
    async with driver.session() as session:
        result = await session.run(check_query, pack_id=pack_id)
        if not await result.single():
            raise HTTPException(status_code=404, detail="Pack not found")

    execution_id = str(uuid.uuid4())
    now = datetime.now(UTC).isoformat()

    # Create execution record
    query = """
    MATCH (vp:ValuePack {id: $pack_id})
    CREATE (pe:PackExecution {
        id: $execution_id,
        packId: $pack_id,
        workspaceId: $workspace_id,
        status: 'running',
        variables: $variables,
        userId: $user_id,
        startedAt: $started_at
    })
    CREATE (vp)-[:HAS_EXECUTION]->(pe)
    RETURN pe
    """

    async with driver.session() as session:
        await session.run(
            query,
            pack_id=pack_id,
            execution_id=execution_id,
            workspace_id=request.workspace_id,
            variables=request.variables,
            user_id=request.user_id,
            started_at=now,
        )

    # NOTE: Formula evaluation integration pending.
    # Pack execution currently records the request but does not evaluate formulas.
    # When formula evaluation is integrated, replace this block with actual evaluation.
    outputs = {
        "pack_id": pack_id,
        "variables_count": len(request.variables),
        "execution_context": request.workspace_id,
    }
    warnings = [
        "Pack execution is partially implemented: variables recorded but formula evaluation not yet active."
    ]

    # Update execution status
    complete_query = """
    MATCH (pe:PackExecution {id: $execution_id})
    SET pe.status = $status,
        pe.outputs = $outputs,
        pe.completedAt = $completed_at
    """

    async with driver.session() as session:
        await session.run(
            complete_query,
            execution_id=execution_id,
            status="success",
            outputs=outputs,
            completed_at=datetime.now(UTC).isoformat(),
        )

    return PackExecuteResponse(
        execution_id=execution_id,
        pack_id=pack_id,
        status="success",
        outputs=outputs,
        errors=[],
        warnings=warnings,
    )


@router.post("/packs/{pack_id}/fork", response_model=PackForkResponse, status_code=201)
async def fork_pack(
    pack_id: str,
    request: PackForkRequest,
    driver: AsyncDriver = Depends(get_driver),
):
    """Fork a Value Pack for customization."""
    import uuid

    # Get original pack
    orig_query = """
    MATCH (vp:ValuePack {id: $pack_id})
    RETURN vp
    """

    async with driver.session() as session:
        result = await session.run(orig_query, pack_id=pack_id)
        record = await result.single()

        if not record:
            raise HTTPException(status_code=404, detail="Pack not found")

        orig = record["vp"]

    # Create forked pack
    new_pack_id = str(uuid.uuid4())
    now = datetime.now(UTC).isoformat()

    # Increment version using shared utility
    original_version = orig.get("version", "1.0.0")
    new_version = increment_patch_version(original_version)

    name = request.name or f"{orig.get('name', 'Unnamed')} (Fork)"

    fork_query = """
    MATCH (old:ValuePack {id: $old_pack_id})
    CREATE (new:ValuePack {
        id: $new_pack_id,
        name: $name,
        description: $description,
        industry: $industry,
        segment: $segment,
        status: $status,
        version: $version,
        workspaceId: $workspace_id,
        isLoaded: true,
        createdAt: $created_at,
        createdBy: $created_by,
        forkedFrom: $old_pack_id
    })
    CREATE (new)-[:SUPERSEDES {type: 'fork'}]->(old)
    WITH new, old
    OPTIONAL MATCH (old)-[:hasDriver]->(vd:ValueDriver)
    FOREACH (d IN CASE WHEN vd IS NOT NULL THEN [vd] ELSE [] END |
        CREATE (new)-[:hasDriver]->(d)
    )
    WITH new, old
    OPTIONAL MATCH (old)-[:hasFormula]->(f:Formula)
    FOREACH (formula IN CASE WHEN f IS NOT NULL THEN [f] ELSE [] END |
        CREATE (new)-[:hasFormula]->(formula)
    )
    WITH new, old
    OPTIONAL MATCH (old)-[:hasBenchmark]->(b:BenchmarkDataset)
    FOREACH (benchmark IN CASE WHEN b IS NOT NULL THEN [b] ELSE [] END |
        CREATE (new)-[:hasBenchmark]->(benchmark)
    )
    RETURN new
    """

    async with driver.session() as session:
        result = await session.run(
            fork_query,
            old_pack_id=pack_id,
            new_pack_id=new_pack_id,
            name=name,
            description=orig.get("description", ""),
            industry=orig.get("industry", ""),
            segment=orig.get("segment"),
            version=new_version,
            status=STATUS_DRAFT,
            workspace_id=request.workspace_id,
            created_at=now,
            created_by=request.user_id,
        )
        record = await result.single()

        if not record:
            raise HTTPException(status_code=500, detail="Failed to fork pack")

        new_pack = record["new"]

        return PackForkResponse(
            pack_id=new_pack["id"],
            name=new_pack["name"],
            version=new_pack["version"],
            status="draft",
        )
