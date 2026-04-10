"""Value Pack Service implementation for Layer 4 Agents.

Neo4j-backed implementation of the Value Pack domain service.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import uuid

from neo4j import AsyncDriver
from neo4j.exceptions import Neo4jError, ServiceUnavailable

logger = logging.getLogger(__name__)

from ..interfaces.value_pack_service import (
    IValuePackService,
    ValuePack,
    ValueDriverRef,
    FormulaRef,
    BenchmarkRef,
    PackExecutionRequest,
    PackExecutionResult,
    PackStatus,
)


class Neo4jValuePackService(IValuePackService):
    """Neo4j-backed Value Pack service implementation."""
    
    def __init__(self, driver: AsyncDriver):
        self._driver = driver
    
    async def list_packs(
        self,
        industry: Optional[str] = None,
        status: Optional[PackStatus] = None,
    ) -> List[ValuePack]:
        """List available Value Packs from Neo4j."""
        query = """
        MATCH (vp:ValuePack)
        WHERE ($industry IS NULL OR vp.industry = $industry)
          AND ($status IS NULL OR vp.status = $status)
        OPTIONAL MATCH (vp)-[:hasDriver]->(vd:ValueDriver)
        OPTIONAL MATCH (vp)-[:hasFormula]->(f:Formula)
        OPTIONAL MATCH (vp)-[:hasBenchmark]->(b:BenchmarkDataset)
        RETURN vp,
               collect(DISTINCT vd) as drivers,
               collect(DISTINCT f) as formulas,
               collect(DISTINCT b) as benchmarks
        """
        
        try:
            async with self._driver.session() as session:
                result = await session.run(
                    query,
                    industry=industry,
                    status=status.value if status else None,
                )
                records = await result.data()
                
                packs = []
                for record in records:
                    vp = record["vp"]
                    drivers = [
                        ValueDriverRef(
                            driver_id=d["id"],
                            name=d.get("name", ""),
                            category=d.get("category", ""),
                            weight=1.0,
                        )
                        for d in record["drivers"]
                        if d
                    ]
                    formulas = [
                        FormulaRef(
                            formula_id=f["id"],
                            name=f.get("name", ""),
                            version=f.get("version", "1.0.0"),
                            variables=f.get("variables", []),
                        )
                        for f in record["formulas"]
                        if f
                    ]
                    benchmarks = [
                        BenchmarkRef(
                            dataset_id=b["id"],
                            metric=b.get("metric", ""),
                            industry=b.get("industry", ""),
                        )
                        for b in record["benchmarks"]
                        if b
                    ]
                    
                    packs.append(ValuePack(
                        pack_id=vp["id"],
                        name=vp.get("name", ""),
                        description=vp.get("description", ""),
                        industry=vp.get("industry", ""),
                        segment=vp.get("segment"),
                        status=PackStatus(vp.get("status", "draft")),
                        version=vp.get("version", "1.0.0"),
                        value_drivers=drivers,
                        formulas=formulas,
                        benchmarks=benchmarks,
                        created_at=datetime.fromisoformat(vp["createdAt"]) if "createdAt" in vp else datetime.now(timezone.utc),
                        updated_at=datetime.fromisoformat(vp["updatedAt"]) if "updatedAt" in vp else None,
                        created_by=vp.get("createdBy"),
                    ))
                
                return packs
        except ServiceUnavailable as e:
            logger.error("Neo4j service unavailable", exc_info=True)
            raise RuntimeError("Database service unavailable") from e
        except Neo4jError as e:
            logger.error(f"Neo4j query failed: {e}", exc_info=True)
            raise RuntimeError(f"Database query failed: {e.code}") from e
    
    async def get_pack(self, pack_id: str) -> Optional[ValuePack]:
        """Retrieve Value Pack by ID from Neo4j."""
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
        
        async with self._driver.session() as session:
            result = await session.run(query, pack_id=pack_id)
            record = await result.single()
            
            if not record:
                return None
            
            vp = record["vp"]
            drivers = [
                ValueDriverRef(
                    driver_id=d["id"],
                    name=d.get("name", ""),
                    category=d.get("category", ""),
                    weight=1.0,
                )
                for d in record["drivers"]
                if d
            ]
            formulas = [
                FormulaRef(
                    formula_id=f["id"],
                    name=f.get("name", ""),
                    version=f.get("version", "1.0.0"),
                    variables=f.get("variables", []),
                )
                for f in record["formulas"]
                if f
            ]
            benchmarks = [
                BenchmarkRef(
                    dataset_id=b["id"],
                    metric=b.get("metric", ""),
                    industry=b.get("industry", ""),
                )
                for b in record["benchmarks"]
                if b
            ]
            
            return ValuePack(
                pack_id=vp["id"],
                name=vp.get("name", ""),
                description=vp.get("description", ""),
                industry=vp.get("industry", ""),
                segment=vp.get("segment"),
                status=PackStatus(vp.get("status", "draft")),
                version=vp.get("version", "1.0.0"),
                value_drivers=drivers,
                formulas=formulas,
                benchmarks=benchmarks,
                created_at=datetime.fromisoformat(vp["createdAt"]) if "createdAt" in vp else datetime.now(timezone.utc),
                updated_at=datetime.fromisoformat(vp["updatedAt"]) if "updatedAt" in vp else None,
                created_by=vp.get("createdBy"),
            )
    
    async def load_pack_into_workspace(
        self,
        pack_id: str,
        workspace_id: str,
    ) -> ValuePack:
        """Load pack into workspace for customization/execution."""
        pack = await self.get_pack(pack_id)
        if not pack:
            raise ValueError(f"Pack {pack_id} not found")
        
        # Mark as loaded in workspace
        query = """
        MATCH (vp:ValuePack {id: $pack_id})
        SET vp.workspaceId = $workspace_id,
            vp.isLoaded = true,
            vp.loadedAt = $loaded_at
        RETURN vp
        """
        
        async with self._driver.session() as session:
            now = datetime.now(timezone.utc).isoformat()
            await session.run(
                query,
                pack_id=pack_id,
                workspace_id=workspace_id,
                now=now,
            )
        
        pack.is_loaded = True
        pack.workspace_id = workspace_id
        return pack
    
    async def execute_pack(
        self,
        request: PackExecutionRequest,
    ) -> PackExecutionResult:
        """Execute pack workflow with provided variables."""
        execution_id = str(uuid.uuid4())
        
        # Get pack
        pack = await self.get_pack(request.pack_id)
        if not pack:
            return PackExecutionResult(
                execution_id=execution_id,
                pack_id=request.pack_id,
                status="failed",
                outputs={},
                errors=[f"Pack {request.pack_id} not found"],
            )
        
        # Store execution context
        query = """
        MATCH (vp:ValuePack {id: $pack_id})
        CREATE (pe:PackExecution {
            id: $execution_id,
            packId: $pack_id,
            workspaceId: $workspace_id,
            status: 'running',
            variables: $variables,
            startedAt: $started_at
        })
        CREATE (vp)-[:HAS_EXECUTION]->(pe)
        RETURN pe
        """
        
        async with self._driver.session() as session:
            started_at = datetime.now(timezone.utc).isoformat()
            await session.run(
                query,
                pack_id=request.pack_id,
                execution_id=execution_id,
                workspace_id=request.workspace_id,
                variables=request.variables,
                started_at=started_at,
            )
        
        # TODO: Integrate with formula evaluation service
        # For now, return placeholder result
        outputs = {
            "pack_name": pack.name,
            "formulas_evaluated": len(pack.formulas),
            "variables_provided": len(request.variables),
        }
        
        # Update execution status
        complete_query = """
        MATCH (pe:PackExecution {id: $execution_id})
        SET pe.status = $status,
            pe.outputs = $outputs,
            pe.completedAt = $completed_at
        """
        
        async with self._driver.session() as session:
            completed_at = datetime.now(timezone.utc).isoformat()
            await session.run(
                complete_query,
                execution_id=execution_id,
                status="success",
                outputs=outputs,
                completed_at=completed_at,
            )
        
        return PackExecutionResult(
            execution_id=execution_id,
            pack_id=request.pack_id,
            status="success",
            outputs=outputs,
            errors=[],
            completed_at=datetime.fromisoformat(completed_at),
        )
    
    async def customize_pack(
        self,
        pack_id: str,
        workspace_id: str,
        modifications: Dict[str, Any],
    ) -> ValuePack:
        """Fork and customize pack for account-specific needs."""
        original = await self.get_pack(pack_id)
        if not original:
            raise ValueError(f"Pack {pack_id} not found")
        
        # Create new pack ID
        new_pack_id = str(uuid.uuid4())
        new_version = self._increment_version(original.version)
        
        query = """
        MATCH (old:ValuePack {id: $old_pack_id})
        CREATE (new:ValuePack {
            id: $new_pack_id,
            name: $name,
            description: $description,
            industry: $industry,
            segment: $segment,
            status: 'draft',
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
        RETURN new
        """
        
        async with self._driver.session() as session:
            created_at = datetime.now(timezone.utc).isoformat()
            result = await session.run(
                query,
                old_pack_id=pack_id,
                new_pack_id=new_pack_id,
                name=modifications.get("name", f"{original.name} (Custom)"),
                description=modifications.get("description", original.description),
                industry=modifications.get("industry", original.industry),
                segment=modifications.get("segment", original.segment),
                version=new_version,
                workspace_id=workspace_id,
                created_at=created_at,
                created_by=modifications.get("user_id"),
            )
            record = await result.single()
            
            if not record:
                raise ValueError("Failed to create customized pack")
            
            new_vp = record["new"]
            
            return ValuePack(
                pack_id=new_vp["id"],
                name=new_vp["name"],
                description=new_vp["description"],
                industry=new_vp["industry"],
                segment=new_vp.get("segment"),
                status=PackStatus.DRAFT,
                version=new_vp["version"],
                created_at=datetime.fromisoformat(new_vp["createdAt"]),
                workspace_id=workspace_id,
                is_loaded=True,
                created_by=new_vp.get("createdBy"),
            )
    
    async def save_pack(self, pack: ValuePack) -> ValuePack:
        """Save pack (create new version or update draft)."""
        query = """
        MERGE (vp:ValuePack {id: $pack_id})
        SET vp.name = $name,
            vp.description = $description,
            vp.industry = $industry,
            vp.segment = $segment,
            vp.status = $status,
            vp.version = $version,
            vp.updatedAt = $updated_at
        RETURN vp
        """
        
        async with self._driver.session() as session:
            result = await session.run(
                query,
                pack_id=pack.pack_id,
                name=pack.name,
                description=pack.description,
                industry=pack.industry,
                segment=pack.segment,
                status=pack.status.value,
                version=pack.version,
                updated_at=datetime.now(timezone.utc).isoformat(),
            )
            record = await result.single()
            
            if record:
                vp = record["vp"]
                pack.updated_at = datetime.fromisoformat(vp["updatedAt"])
            
            return pack
    
    def _increment_version(self, version: str) -> str:
        """Increment patch version number."""
        parts = version.split(".")
        if len(parts) >= 3:
            try:
                major, minor, patch = parts[0], parts[1], int(parts[2])
                return f"{major}.{minor}.{patch + 1}"
            except ValueError:
                pass
        return "1.0.0"
