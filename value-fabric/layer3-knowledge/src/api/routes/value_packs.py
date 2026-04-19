"""Value Pack API routes for Layer 3.

Provides endpoints for Value Pack CRUD and execution.
"""

import re
import uuid
from datetime import UTC, datetime
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from neo4j import AsyncDriver
from pydantic import BaseModel, Field

from ...db.driver import get_driver
from ...logging_config import get_logger
from ...api.routes.formulas import evaluate_expression, FORMULA_REGISTRY
from ._utils import increment_patch_version

logger = get_logger(__name__)

# Status constants for Value Packs
STATUS_DRAFT = "draft"
STATUS_PUBLISHED = "published"
STATUS_DEPRECATED = "deprecated"
STATUS_ARCHIVED = "archived"

# Relationship type constants for Neo4j
REL_HAS_DRIVER = "hasDriver"
REL_HAS_FORMULA = "hasFormula"
REL_HAS_BENCHMARK = "hasBenchmark"
REL_HAS_WORKFLOW = "hasWorkflow"
REL_SUPERSEDES = "SUPERSEDES"
REL_HAS_EXECUTION = "HAS_EXECUTION"

# Default version for new packs
DEFAULT_VERSION = "1.0.0"

# Pagination limits
MAX_PAGE_SIZE = 100
DEFAULT_PAGE_SIZE = 50


# Pack ID validation regex: allows UUIDs OR slug-style IDs (alphanumeric, hyphens, underscores)
# Examples: "manufacturing-v1", "life-sciences-v1", "550e8400-e29b-41d4-a716-446655440000"
VALID_PACK_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_-]+$')
MAX_PACK_ID_LENGTH = 128


def _validate_pack_id(pack_id: str) -> None:
    """Validate pack_id format.

    Accepts both UUID format (for dynamic packs) and slug-style IDs
    (for manifest packs like "manufacturing-v1").

    Raises:
        HTTPException: 400 if pack_id format is invalid or too long.
    """
    if not pack_id:
        raise HTTPException(status_code=400, detail="pack_id is required")

    if len(pack_id) > MAX_PACK_ID_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"pack_id exceeds maximum length ({MAX_PACK_ID_LENGTH} chars): {pack_id[:50]}..."
        )

    # Check if it's a valid UUID
    try:
        uuid.UUID(pack_id)
        return  # Valid UUID
    except ValueError:
        pass  # Not a UUID, check slug format

    # Check slug format (alphanumeric, hyphens, underscores)
    if not VALID_PACK_ID_PATTERN.match(pack_id):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid pack_id format: {pack_id}. Must be UUID or slug-style (alphanumeric, hyphens, underscores)."
        )

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
    workflow_count: int = 0
    scope: str | None = "global"
    category: str | None = None
    updated_at: str | None = None
    created_by: str | None = None


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
    workflow_count: int = 0
    scope: str | None = "global"
    category: str | None = None


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


async def _update_relationships(
    tx,
    pack_id: str,
    rel_type: str,
    target_label: str,
    target_ids: list[str],
) -> None:
    """Update pack relationships, validating target entities exist.

    Raises HTTPException if any target_id doesn't exist.
    """
    # Validate all targets exist
    if target_ids:
        check_query = f"""
        UNWIND $target_ids as target_id
        MATCH (t:{target_label} {{id: target_id}})
        RETURN collect(t.id) as found_ids
        """
        result = await tx.run(check_query, target_ids=target_ids)
        record = await result.single()
        found_ids = set(record["found_ids"]) if record else set()
        missing = set(target_ids) - found_ids
        if missing:
            raise HTTPException(
                status_code=400,
                detail=f"{target_label} IDs not found: {sorted(missing)}"
            )

    # Delete existing relationships
    delete_query = f"""
    MATCH (vp:ValuePack {{id: $pack_id}})
    OPTIONAL MATCH (vp)-[r:{rel_type}]->()
    DELETE r
    """
    await tx.run(delete_query, pack_id=pack_id)

    # Create new relationships
    create_query = f"""
    MATCH (vp:ValuePack {{id: $pack_id}})
    UNWIND $target_ids as target_id
    MATCH (t:{target_label} {{id: target_id}})
    CREATE (vp)-[:{rel_type}]->(t)
    """
    await tx.run(create_query, pack_id=pack_id, target_ids=target_ids)


async def _get_pack_detail(driver: AsyncDriver, pack_id: str) -> PackDetail | None:
    """Get full pack detail from Neo4j.

    Returns None if pack not found, PackDetail with related entities otherwise.
    """
    query = """
    MATCH (vp:ValuePack {id: $pack_id})
    OPTIONAL MATCH (vp)-[:hasDriver]->(vd:ValueDriver)
    OPTIONAL MATCH (vp)-[:hasFormula]->(f:Formula)
    OPTIONAL MATCH (vp)-[:hasBenchmark]->(b:BenchmarkDataset)
    OPTIONAL MATCH (vp)-[:hasWorkflow]->(w:Workflow)
    RETURN vp,
           collect(DISTINCT vd) as drivers,
           collect(DISTINCT f) as formulas,
           collect(DISTINCT b) as benchmarks,
           count(DISTINCT w) as workflow_count
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
                version=f.get("version", DEFAULT_VERSION),
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
            version=vp.get("version", DEFAULT_VERSION),
            drivers=drivers,
            formulas=formulas,
            benchmarks=benchmarks,
            created_at=vp.get("createdAt", datetime.now(UTC).isoformat()),
            updated_at=vp.get("updatedAt"),
            created_by=vp.get("createdBy"),
            workspace_id=vp.get("workspaceId"),
            is_loaded=vp.get("isLoaded", False),
            workflow_count=record["workflow_count"],
            scope=vp.get("scope", "global"),
            category=vp.get("category"),
        )


# API Endpoints


@router.get("/packs", response_model=list[PackSummary])
async def list_packs(
    industry: str | None = Query(None, description="Filter by industry"),
    status: str | None = Query(None, description="Filter by status"),
    category: str | None = Query(None, description="Filter by category"),
    search: str | None = Query(None, description="Search by name or description"),
    limit: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE, description="Maximum results to return"),
    driver: AsyncDriver = Depends(get_driver),
):
    """List available Value Packs."""
    query = """
    MATCH (vp:ValuePack)
    WHERE ($industry IS NULL OR vp.industry = $industry)
      AND ($status IS NULL OR vp.status = $status)
      AND ($category IS NULL OR vp.category = $category)
      AND ($search IS NULL OR 
           toLower(vp.name) CONTAINS toLower($search) OR 
           toLower(vp.description) CONTAINS toLower($search))
    OPTIONAL MATCH (vp)-[:hasDriver]->(vd:ValueDriver)
    OPTIONAL MATCH (vp)-[:hasFormula]->(f:Formula)
    OPTIONAL MATCH (vp)-[:hasBenchmark]->(b:BenchmarkDataset)
    OPTIONAL MATCH (vp)-[:hasWorkflow]->(w:Workflow)
    RETURN vp,
           count(DISTINCT vd) as driver_count,
           count(DISTINCT f) as formula_count,
           count(DISTINCT b) as benchmark_count,
           count(DISTINCT w) as workflow_count
    ORDER BY vp.name
    LIMIT $limit
    """

    async with driver.session() as session:
        result = await session.run(
            query,
            industry=industry,
            status=status,
            category=category,
            search=search,
            limit=limit,
        )
        records = await result.data()

        return [
            PackSummary(
                pack_id=r["vp"]["id"],
                name=r["vp"].get("name", ""),
                industry=r["vp"].get("industry", ""),
                segment=r["vp"].get("segment"),
                status=r["vp"].get("status", "draft"),
                version=r["vp"].get("version", DEFAULT_VERSION),
                driver_count=r["driver_count"],
                formula_count=r["formula_count"],
                benchmark_count=r["benchmark_count"],
                workflow_count=r["workflow_count"],
                scope=r["vp"].get("scope", "global"),
                category=r["vp"].get("category"),
                updated_at=r["vp"].get("updatedAt"),
                created_by=r["vp"].get("createdBy"),
            )
            for r in records
        ]


@router.get("/packs/{pack_id}", response_model=PackDetail)
async def get_pack(
    pack_id: str,
    driver: AsyncDriver = Depends(get_driver),
):
    """Get Value Pack by ID."""
    _validate_pack_id(pack_id)
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
        version: $default_version,
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
    WITH vp
    OPTIONAL MATCH (vp)-[:hasDriver]->(vd2:ValueDriver)
    OPTIONAL MATCH (vp)-[:hasFormula]->(f2:Formula)
    OPTIONAL MATCH (vp)-[:hasBenchmark]->(b2:BenchmarkDataset)
    RETURN vp,
           collect(DISTINCT vd2) as drivers,
           collect(DISTINCT f2) as formulas,
           collect(DISTINCT b2) as benchmarks
    """

    async with driver.session() as session:
        async with session.begin_transaction() as tx:
            result = await tx.run(
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
                default_version=DEFAULT_VERSION,
            )
            record = await result.single()
            if not record:
                raise HTTPException(status_code=500, detail="Failed to create pack")

            vp = record["vp"]

            # Build relationship summaries from returned data
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
                    version=f.get("version", DEFAULT_VERSION),
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
                name=vp.get("name", request.name),
                description=vp.get("description", request.description),
                industry=vp.get("industry", request.industry),
                segment=vp.get("segment", request.segment),
                status=vp.get("status", request.status),
                version=vp.get("version", DEFAULT_VERSION),
                drivers=drivers,
                formulas=formulas,
                benchmarks=benchmarks,
                created_at=vp.get("createdAt", now),
                updated_at=vp.get("updatedAt"),
                created_by=vp.get("createdBy", request.created_by),
                workspace_id=vp.get("workspaceId"),
                is_loaded=False,
                workflow_count=0,
                scope=vp.get("scope", "global"),
                category=vp.get("category"),
            )


def _build_update_params(
    request: PackUpdateRequest, pack_id: str
) -> tuple[list[str], dict[str, Any]]:
    """Build SET clauses and params for pack update query.

    Returns:
        Tuple of (set_clauses list, params dict)
    """
    set_clauses = ["vp.updatedAt = $updated_at"]
    params: dict[str, Any] = {
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

    return set_clauses, params


async def _update_pack_relationships(
    tx, pack_id: str, request: PackUpdateRequest
) -> None:
    """Update pack relationships if provided in request.

    Validates target entities exist before creating relationships.
    """
    if request.driver_ids is not None:
        await _update_relationships(
            tx, pack_id, "hasDriver", "ValueDriver", request.driver_ids
        )
    if request.formula_ids is not None:
        await _update_relationships(
            tx, pack_id, "hasFormula", "Formula", request.formula_ids
        )
    if request.benchmark_ids is not None:
        await _update_relationships(
            tx, pack_id, "hasBenchmark", "BenchmarkDataset", request.benchmark_ids
        )


@router.put("/packs/{pack_id}", response_model=PackDetail)
async def update_pack(
    pack_id: str,
    request: PackUpdateRequest,
    driver: AsyncDriver = Depends(get_driver),
):
    """Update a Value Pack."""
    _validate_pack_id(pack_id)

    # Verify pack exists
    check_query = "MATCH (vp:ValuePack {id: $pack_id}) RETURN vp"
    async with driver.session() as session:
        result = await session.run(check_query, pack_id=pack_id)
        if not await result.single():
            raise HTTPException(status_code=404, detail="Pack not found")

    # Build and execute update
    set_clauses, params = _build_update_params(request, pack_id)
    update_query = f"""
    MATCH (vp:ValuePack {{id: $pack_id}})
    SET {", ".join(set_clauses)}
    RETURN vp
    """

    async with driver.session() as session:
        async with session.begin_transaction() as tx:
            await tx.run(update_query, **params)
            await _update_pack_relationships(tx, pack_id, request)

        # Re-query for consistent view with relationships
        pack = await _get_pack_detail(driver, pack_id)
        if not pack:
            raise HTTPException(status_code=500, detail="Failed to update pack")
        return pack


async def _get_pack_formulas(
    driver: AsyncDriver, pack_id: str
) -> list[dict[str, Any]]:
    """Get all formulas associated with a pack from Neo4j.

    Returns list of formula dicts with id, expression, variables, name.
    """
    query = """
    MATCH (vp:ValuePack {id: $pack_id})-[:hasFormula]->(f:Formula)
    RETURN f.id as formula_id,
           f.expression as expression,
           f.variables as variables,
           f.name as name
    """
    async with driver.session() as session:
        result = await session.run(query, pack_id=pack_id)
        records = await result.data()
        return records


def _merge_variables(
    formula_defaults: list[dict], user_variables: dict[str, Any]
) -> dict[str, float]:
    """Merge user-provided variables with formula defaults.

    Args:
        formula_defaults: List of variable dicts with 'name' and 'default_value'
        user_variables: Dict of user-provided variable values

    Returns:
        Merged dict with all required variables as floats
    """
    merged: dict[str, float] = {}

    # Add formula defaults first
    for var in formula_defaults:
        var_name = var.get("name")
        default = var.get("default_value")
        if var_name and default is not None:
            try:
                merged[var_name] = float(default)
            except (ValueError, TypeError):
                logger.warning(
                    f"Invalid default value for variable '{var_name}': {default!r}. Skipping."
                )

    # Override with user-provided values
    for var_name, var_value in user_variables.items():
        try:
            merged[var_name] = float(var_value)
        except (ValueError, TypeError):
            if var_name in merged:
                logger.warning(
                    f"Invalid user value for variable '{var_name}': {var_value!r}. "
                    f"Keeping default: {merged[var_name]}."
                )
            else:
                logger.warning(
                    f"Invalid user value for variable '{var_name}': {var_value!r}. "
                    f"No default available, skipping."
                )

    return merged


@router.post("/packs/{pack_id}/execute", response_model=PackExecuteResponse)
async def execute_pack(
    pack_id: str,
    request: PackExecuteRequest,
    driver: AsyncDriver = Depends(get_driver),
):
    """Execute a Value Pack workflow.

    Evaluates all formulas associated with the pack using provided variables
    merged with formula defaults. Returns calculated values for each formula.
    """
    _validate_pack_id(pack_id)
    execution_id = str(uuid.uuid4())
    now = datetime.now(UTC).isoformat()

    # Get pack formulas
    pack_formulas = await _get_pack_formulas(driver, pack_id)

    if not pack_formulas:
        raise HTTPException(
            status_code=400,
            detail=f"Pack {pack_id} has no formulas to execute"
        )

    # Create execution record
    create_query = """
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
        result = await session.run(
            create_query,
            pack_id=pack_id,
            execution_id=execution_id,
            workspace_id=request.workspace_id,
            variables=request.variables,
            user_id=request.user_id,
            started_at=now,
        )
        if not await result.single():
            raise HTTPException(status_code=500, detail="Failed to create execution record")

    # Execute formulas
    outputs: dict[str, Any] = {"pack_id": pack_id, "formulas_evaluated": 0}
    errors: list[str] = []
    warnings: list[str] = []
    execution_status = "success"

    for formula in pack_formulas:
        formula_id = formula.get("formula_id", "unknown")
        expression = formula.get("expression", "")
        variables_spec = formula.get("variables", []) or []
        formula_name = formula.get("name", formula_id)

        if not expression:
            errors.append(f"Formula '{formula_name}' has no expression")
            continue

        # Build variable context: merge user inputs with formula defaults
        variable_context = _merge_variables(variables_spec, request.variables)

        try:
            result_value = evaluate_expression(expression, variable_context)
            outputs[formula_id] = {
                "name": formula_name,
                "result": result_value,
                "expression": expression,
                "variables_used": variable_context,
            }
            outputs["formulas_evaluated"] += 1
        except ValueError as e:
            errors.append(f"Formula '{formula_name}' evaluation failed: {e}")
            execution_status = "partial"
        except Exception as e:
            errors.append(f"Formula '{formula_name}' unexpected error: {e}")
            execution_status = "partial"

    # Determine final status
    if outputs["formulas_evaluated"] == 0 and errors:
        execution_status = "failed"
    elif errors:
        execution_status = "partial"

    # Update execution record with results
    complete_query = """
    MATCH (pe:PackExecution {id: $execution_id})
    SET pe.status = $status,
        pe.outputs = $outputs,
        pe.errors = $errors,
        pe.completedAt = $completed_at
    """

    async with driver.session() as session:
        async with session.begin_transaction() as tx:
            await tx.run(
                complete_query,
                execution_id=execution_id,
                status=execution_status,
                outputs=outputs,
                errors=errors,
                completed_at=datetime.now(UTC).isoformat(),
            )

    return PackExecuteResponse(
        execution_id=execution_id,
        pack_id=pack_id,
        status=execution_status,
        outputs=outputs,
        errors=errors,
        warnings=warnings,
    )


async def _get_original_pack(
    driver: AsyncDriver, pack_id: str
) -> dict[str, Any]:
    """Get original pack data for forking.

    Raises HTTPException if pack not found.
    """
    query = "MATCH (vp:ValuePack {id: $pack_id}) RETURN vp"
    async with driver.session() as session:
        result = await session.run(query, pack_id=pack_id)
        record = await result.single()
        if not record:
            raise HTTPException(status_code=404, detail="Pack not found")
        return record["vp"]


def _build_fork_params(
    orig: dict[str, Any], request: PackForkRequest, new_pack_id: str
) -> dict[str, Any]:
    """Build parameters for fork creation query.

    Returns dict with all parameters for the fork Cypher query.
    """
    original_version = orig.get("version", DEFAULT_VERSION)
    new_version = increment_patch_version(original_version)
    name = request.name or f"{orig.get('name', 'Unnamed')} (Fork)"
    now = datetime.now(UTC).isoformat()

    return {
        "old_pack_id": orig["id"],
        "new_pack_id": new_pack_id,
        "name": name,
        "description": orig.get("description", ""),
        "industry": orig.get("industry", ""),
        "segment": orig.get("segment"),
        "version": new_version,
        "status": STATUS_DRAFT,
        "workspace_id": request.workspace_id,
        "created_at": now,
        "created_by": request.user_id,
    }


async def _execute_fork(
    driver: AsyncDriver, params: dict[str, Any]
) -> dict[str, Any]:
    """Execute fork creation in Neo4j.

    Creates new pack with relationships copied from original.
    Returns the new pack node properties.

    Raises HTTPException on failure.
    """
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
        result = await session.run(fork_query, **params)
        record = await result.single()
        if not record:
            raise HTTPException(status_code=500, detail="Failed to fork pack")
        return record["new"]


@router.post("/packs/{pack_id}/fork", response_model=PackForkResponse, status_code=201)
async def fork_pack(
    pack_id: str,
    request: PackForkRequest,
    driver: AsyncDriver = Depends(get_driver),
):
    """Fork a Value Pack for customization."""
    _validate_pack_id(pack_id)

    # Get original pack properties
    orig = await _get_original_pack(driver, pack_id)

    # Create forked pack with copied relationships
    new_pack_id = str(uuid.uuid4())
    fork_params = _build_fork_params(orig, request, new_pack_id)
    new_pack = await _execute_fork(driver, fork_params)

    return PackForkResponse(
        pack_id=new_pack["id"],
        name=new_pack["name"],
        version=new_pack["version"],
        status=STATUS_DRAFT,
    )


@router.post("/packs/{pack_id}/apply", response_model=PackExecuteResponse)
async def apply_pack(
    pack_id: str,
    request: PackExecuteRequest,
    driver: AsyncDriver = Depends(get_driver),
):
    """Apply/Deploy a Value Pack (alias for execute endpoint)."""
    _validate_pack_id(pack_id)
    # NOTE: apply_pack is currently an alias for execute_pack.
    # When execution logic diverges (e.g., deployment vs preview), refactor.
    return await execute_pack(pack_id, request, driver)
