"""State consistency gate plugin."""

import json
from pathlib import Path

from sdk.models import CheckResult, GateResult, GateSeverity
from sdk.plugin import GateContext, GatePlugin


class StateGate(GatePlugin):
    """Gate for state consistency validation."""
    
    @property
    def gate_id(self) -> str:
        return "state"
    
    @property
    def severity(self) -> GateSeverity:
        return GateSeverity.BLOCKER
    
    @property
    def expected_artifacts(self) -> list[str]:
        return [
            "state/report.json",
            "state/summary.md",
        ]
    
    def execute(self, ctx: GateContext) -> list[CheckResult]:
        """Run state consistency checks."""
        results = []
        
        # Check 1: Layer 3 Neo4j schema consistency
        l3_schema = self._check_l3_schema(ctx.workspace_dir)
        results.append(CheckResult(
            name="layer3_schema",
            result=GateResult.PASS if l3_schema["consistent"] else GateResult.FAIL,
            value=l3_schema.get("constraint_count", 0),
            threshold=5,
            comparator="gte",
            message=f"L3 Neo4j constraints: {l3_schema.get('constraint_count', 0)}",
        ))
        
        # Check 2: Layer 4 checkpoint/resume capability
        checkpoint = self._check_checkpoint_system(ctx.workspace_dir)
        results.append(CheckResult(
            name="checkpoint_system",
            result=GateResult.PASS if checkpoint["exists"] else GateResult.FAIL,
            value=checkpoint.get("test_count", 0),
            threshold=1,
            comparator="gte",
            message=f"Checkpoint tests: {checkpoint.get('test_count', 0)}",
        ))
        
        # Check 3: Database migrations are valid
        migrations = self._check_migrations(ctx.workspace_dir)
        results.append(CheckResult(
            name="database_migrations",
            result=GateResult.PASS if migrations["valid"] else GateResult.FAIL,
            value=migrations.get("migration_count", 0),
            threshold=3,
            comparator="gte",
            message=f"Valid migrations: {migrations.get('migration_count', 0)}",
        ))
        
        # Check 4: Tenant isolation in state
        tenant_iso = self._check_tenant_isolation(ctx.workspace_dir)
        results.append(CheckResult(
            name="tenant_isolation",
            result=GateResult.PASS if tenant_iso["isolated"] else GateResult.FAIL,
            value=tenant_iso.get("isolation_score", 0.0),
            threshold=0.95,
            comparator="gte",
            message=f"Tenant isolation: {tenant_iso.get('isolation_score', 0):.1%}",
        ))
        
        # Check 5: Consistent entity IDs across layers
        entity_ids = self._check_entity_id_consistency(ctx.workspace_dir)
        results.append(CheckResult(
            name="entity_id_consistency",
            result=GateResult.PASS if entity_ids["consistent"] else GateResult.FAIL,
            value=entity_ids.get("consistency_score", 0.0),
            threshold=1.0,
            comparator="eq",
            message=f"Entity ID consistency: {entity_ids.get('consistency_score', 0):.1%}",
        ))
        
        return results
    
    def _check_l3_schema(self, workspace: Path) -> dict:
        """Check Layer 3 Neo4j schema."""
        # Look for constraint definitions
        constraints_file = workspace / "value-fabric/layer3-knowledge/src/db/neo4j/constraints.py"
        
        if not constraints_file.exists():
            return {"consistent": False, "constraint_count": 0}
        
        content = constraints_file.read_text()
        
        # Count constraint definitions
        constraint_count = content.count("CREATE CONSTRAINT") + content.count("constraint")
        
        return {
            "consistent": constraint_count >= 5,
            "constraint_count": constraint_count,
        }
    
    def _check_checkpoint_system(self, workspace: Path) -> dict:
        """Check Layer 4 checkpoint/resume tests."""
        checkpoint_test = workspace / "value-fabric/layer4-agents/tests/test_checkpoint_resume.py"
        checkpoint_service = workspace / "value-fabric/layer4-agents/src/services/checkpoint.py"
        
        exists = checkpoint_service.exists()
        test_count = 0
        
        if checkpoint_test.exists():
            content = checkpoint_test.read_text()
            test_count = content.count("def test_")
        
        return {
            "exists": exists,
            "test_count": test_count,
        }
    
    def _check_migrations(self, workspace: Path) -> dict:
        """Check database migrations."""
        migration_dirs = [
            workspace / "value-fabric/layer1-ingestion/migrations",
            workspace / "value-fabric/layer2-extraction/migrations",
            workspace / "value-fabric/layer3-knowledge/migrations",
            workspace / "value-fabric/layer4-agents/migrations",
        ]
        
        total_migrations = 0
        
        for mig_dir in migration_dirs:
            if mig_dir.exists():
                migration_files = list(mig_dir.glob("*.py"))
                total_migrations += len([f for f in migration_files if not f.name.startswith("__")])
        
        return {
            "valid": total_migrations >= 3,
            "migration_count": total_migrations,
        }
    
    def _check_tenant_isolation(self, workspace: Path) -> dict:
        """Check tenant isolation implementation."""
        # Look for tenant isolation patterns
        tenant_patterns = [
            workspace / "shared/identity/context.py",
            workspace / "shared/identity/dependencies.py",
        ]
        
        isolation_score = 0.0
        found_files = 0
        
        for pattern in tenant_patterns:
            if pattern.exists():
                found_files += 1
                content = pattern.read_text()
                # Check for tenant isolation patterns
                if "tenant_id" in content and "get_tenant_context" in content:
                    isolation_score += 0.5
        
        return {
            "isolated": isolation_score >= 0.95,
            "isolation_score": min(isolation_score, 1.0),
            "files_found": found_files,
        }
    
    def _check_entity_id_consistency(self, workspace: Path) -> dict:
        """Check entity ID consistency across layers."""
        # Look for consistent entity ID patterns
        id_patterns_found = 0
        
        # Check Layer 3 for entity ID handling
        l3_api = workspace / "value-fabric/layer3-knowledge/src/api/main.py"
        if l3_api.exists():
            content = l3_api.read_text()
            if "entity_id" in content and "tenant_id" in content:
                id_patterns_found += 1
        
        # Check Layer 4 for entity ID handling
        l4_api = workspace / "value-fabric/layer4-agents/src/api/main.py"
        if l4_api.exists():
            content = l4_api.read_text()
            if "entity_id" in content:
                id_patterns_found += 1
        
        consistency_score = id_patterns_found / 2 if id_patterns_found > 0 else 0.0
        
        return {
            "consistent": consistency_score == 1.0,
            "consistency_score": consistency_score,
        }
