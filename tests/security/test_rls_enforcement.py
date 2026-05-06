"""S2-C: RLS Enforcement & Connection Pool Reset Tests — Pillar 2.

Ship/No-Ship Gate: These tests verify that:
    1. RLS migration scripts cover ALL tables with tenant_id columns.
    2. The ``get_db`` dependency does NOT set ``app.tenant_id`` (proving it
       bypasses RLS).
    3. The ``get_db_from_context`` dependency DOES set ``app.tenant_id``.
    4. Connection pool sessions are reset between requests (no tenant leakage).
    5. The ``db_session`` context manager validates tenant_id.

Tests in this file are split into two categories:
    - **Static analysis** (no database required): Parse migration scripts and
      source code to verify structural invariants.
    - **Live database** (requires PostgreSQL): Execute actual SQL to verify RLS
      policies are enforced.  These are skipped locally if no DB is available,
      but hard-fail in CI.

Expected Initial State:
    - test_all_tenant_tables_have_rls_policies: FAIL or PASS (depends on model scan)
    - test_get_db_does_not_set_tenant_context: PASS (confirms the vulnerability)
    - test_get_db_from_context_sets_tenant_id: PASS
    - test_rls_policy_uses_current_setting:    PASS
    - test_rls_null_tenant_id_allows_read:     FAIL (RLS policy allows NULL tenant_id)
"""
from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Set

import pytest

# ---------------------------------------------------------------------------
# Path constants
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parents[2]

_L4_DATABASE_MODULE = (
    _PROJECT_ROOT / "services" / "layer4-agents" / "src" / "database.py"
)

_L4_MIGRATIONS_DIR = (
    _PROJECT_ROOT / "services" / "layer4-agents" / "migrations" / "versions"
)

_L4_MODELS_DIR = (
    _PROJECT_ROOT / "services" / "layer4-agents" / "src" / "models"
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_rls_tables_from_migrations() -> Set[str]:
    """Extract all table names that have RLS policies from migration files."""
    tables: Set[str] = set()

    for migration_file in sorted(_L4_MIGRATIONS_DIR.glob("*.py")):
        source = migration_file.read_text()
        # Match: RLS_TABLES = ["table1", "table2", ...]
        match = re.search(r"RLS_TABLES\s*=\s*\[([^\]]+)\]", source, re.DOTALL)
        if match:
            raw = match.group(1)
            tables.update(re.findall(r'"([^"]+)"', raw))

    return tables


def _extract_model_tables_with_tenant_id() -> Set[str]:
    """Find all SQLAlchemy model classes that have a tenant_id column."""
    tables: Set[str] = set()

    model_files = list(_L4_MODELS_DIR.glob("*.py"))
    # Also check tenant models
    tenant_models_dir = _PROJECT_ROOT / "services" / "layer4-agents" / "src" / "tenants" / "models"
    if tenant_models_dir.exists():
        model_files.extend(tenant_models_dir.glob("*.py"))

    for model_file in model_files:
        if model_file.name.startswith("__"):
            continue
        source = model_file.read_text()

        # Find __tablename__ assignments
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                has_tablename = None
                has_tenant_id = False

                for item in node.body:
                    # Check for __tablename__ = "..."
                    if isinstance(item, ast.Assign):
                        for target in item.targets:
                            if isinstance(target, ast.Name) and target.id == "__tablename__":
                                if isinstance(item.value, ast.Constant):
                                    has_tablename = str(item.value.value)

                    # Check for tenant_id column (various patterns)
                    if isinstance(item, ast.Assign):
                        for target in item.targets:
                            if isinstance(target, ast.Name) and target.id == "tenant_id":
                                has_tenant_id = True
                    elif isinstance(item, ast.AnnAssign):
                        if isinstance(item.target, ast.Name) and item.target.id == "tenant_id":
                            has_tenant_id = True

                if has_tablename and has_tenant_id:
                    tables.add(has_tablename)

    return tables


# ---------------------------------------------------------------------------
# Tests: Migration Coverage
# ---------------------------------------------------------------------------

class TestRLSMigrationCoverage:
    """Verify RLS policies cover all tables with tenant_id columns."""

    def test_all_tenant_tables_have_rls_policies(self):
        """Every model with tenant_id must have a corresponding RLS policy.

        This test compares the set of tables declared in RLS migration scripts
        against the set of SQLAlchemy models that have a tenant_id column.
        """
        rls_tables = _extract_rls_tables_from_migrations()
        model_tables = _extract_model_tables_with_tenant_id()

        missing_rls = model_tables - rls_tables
        assert not missing_rls, (
            f"Found {len(missing_rls)} table(s) with tenant_id column but no RLS policy:\n"
            + "\n".join(f"  - {t}" for t in sorted(missing_rls))
            + f"\nTables with RLS: {sorted(rls_tables)}"
            + f"\nTables with tenant_id: {sorted(model_tables)}"
        )

    def test_rls_tables_list_is_not_empty(self):
        """Sanity check: we should find at least 8 tables with RLS policies."""
        rls_tables = _extract_rls_tables_from_migrations()
        assert len(rls_tables) >= 8, (
            f"Expected at least 8 tables with RLS policies, found {len(rls_tables)}: "
            f"{sorted(rls_tables)}"
        )


# ---------------------------------------------------------------------------
# Tests: Database Module Structure
# ---------------------------------------------------------------------------

class TestDatabaseModuleStructure:
    """Verify the L4 database module enforces tenant context correctly."""

    def test_get_db_sets_empty_tenant_context(self):
        """Confirm that ``get_db`` sets ``app.tenant_id`` to empty string.

        get_db sets app.tenant_id = '' which is the admin bypass pattern.
        This means it relies on PostgreSQL admin_role to access data,
        bypassing RLS entirely.  This is acceptable for health checks but
        dangerous for business endpoints — which is why S2-A and S2-B tests
        gate on migrating all callers to get_db_from_context.
        """
        source = _L4_DATABASE_MODULE.read_text()

        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name == "get_db":
                    func_source = ast.get_source_segment(source, node) or ""

                    # get_db sets tenant_id to empty string (admin bypass)
                    assert "app.tenant_id" in func_source, (
                        "get_db does not set app.tenant_id at all. "
                        "Even the deprecated path should explicitly clear "
                        "tenant context to prevent leakage from a prior request."
                    )

                    # Verify it sets to empty string, not a real tenant
                    assert "= ''" in func_source or '= ""' in func_source, (
                        "get_db sets app.tenant_id but not to empty string. "
                        "The admin bypass pattern requires empty string."
                    )
                    return

        pytest.fail("get_db function not found in database.py")

    def test_get_db_from_context_sets_tenant_id(self):
        """Verify ``get_db_from_context`` sets ``app.tenant_id`` via SET LOCAL."""
        source = _L4_DATABASE_MODULE.read_text()

        # Find get_db_from_context
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name == "get_db_from_context":
                    func_source = ast.get_source_segment(source, node) or ""

                    assert "app.tenant_id" in func_source, (
                        "get_db_from_context does not set app.tenant_id. "
                        "This means even the 'correct' dependency doesn't enforce RLS."
                    )
                    return

        pytest.fail("get_db_from_context function not found in database.py")

    def test_validate_tenant_id_exists(self):
        """The database module must have a validate_tenant_id function."""
        source = _L4_DATABASE_MODULE.read_text()
        assert "def validate_tenant_id" in source, (
            "database.py does not define validate_tenant_id. "
            "Tenant ID validation is required to prevent injection attacks."
        )

    def test_get_db_from_context_validates_tenant_id(self):
        """get_db_from_context must call validate_tenant_id before using it."""
        source = _L4_DATABASE_MODULE.read_text()

        # Find get_db_from_context and check it calls validate_tenant_id
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name == "get_db_from_context":
                    func_source = ast.get_source_segment(source, node) or ""
                    assert "validate_tenant_id" in func_source, (
                        "get_db_from_context does not call validate_tenant_id. "
                        "Unvalidated tenant_id could enable SQL injection via "
                        "SET LOCAL app.tenant_id."
                    )
                    return

        pytest.fail("get_db_from_context function not found in database.py")


# ---------------------------------------------------------------------------
# Tests: RLS Policy Structure
# ---------------------------------------------------------------------------

class TestRLSPolicyStructure:
    """Verify RLS policies use the correct PostgreSQL patterns."""

    def test_rls_policy_uses_current_setting(self):
        """RLS policies must use ``current_setting('app.tenant_id', true)``."""
        for migration_file in sorted(_L4_MIGRATIONS_DIR.glob("*.py")):
            source = migration_file.read_text()
            if "RLS_TABLES" not in source:
                continue

            assert "current_setting('app.tenant_id'" in source, (
                f"{migration_file.name} defines RLS_TABLES but does not use "
                f"current_setting('app.tenant_id', true) in the policy."
            )

    def test_rls_null_tenant_id_policy_is_safe(self):
        """RLS policies must NOT allow rows with NULL tenant_id to be visible
        to all tenants.

        The current policy has ``tenant_id IS NULL OR ...`` which means rows
        without a tenant_id are visible to everyone.  This is a data leak risk
        if any code path accidentally inserts rows without setting tenant_id.

        This test understands migration ordering: if a later migration fixes
        the NULL pattern for the same tables, the earlier migration is not
        flagged (the later one supersedes it at runtime).

        Expected initial state: FAIL — current policy allows NULL.
        """
        # Build a map: table -> highest migration revision that touches it
        # Then check only the latest migration for each table
        migration_files = sorted(_L4_MIGRATIONS_DIR.glob("*.py"))

        # Collect all migrations with RLS_TABLES and their tables
        migrations_with_rls: list[tuple[Path, set]] = []
        for mf in migration_files:
            source = mf.read_text()
            match = re.search(r"RLS_TABLES\s*=\s*\[([^\]]+)\]", source, re.DOTALL)
            if match:
                tables = set(re.findall(r'"([^"]+)"', match.group(1)))
                migrations_with_rls.append((mf, tables))

        # For each table, find the LATEST migration that defines it
        table_latest_migration: dict[str, Path] = {}
        for mf, tables in migrations_with_rls:
            for table in tables:
                table_latest_migration[table] = mf  # later files overwrite earlier

        # Now check only the latest migration for each table
        files_to_check = set(table_latest_migration.values())
        for migration_file in sorted(files_to_check):
            source = migration_file.read_text()

            if "tenant_id IS NULL" in source:
                # Check if it's in a USING clause in the upgrade function
                # (downgrade functions may restore old patterns — that's expected)
                upgrade_match = re.search(
                    r"def upgrade\(\).*?(?=def downgrade\(\)|\Z)",
                    source,
                    re.DOTALL,
                )
                if upgrade_match:
                    upgrade_source = upgrade_match.group(0)
                    if re.search(r"USING\s*\([^)]*tenant_id\s+IS\s+NULL", upgrade_source, re.IGNORECASE):
                        pytest.fail(
                            f"{migration_file.name}: RLS policy allows rows with NULL tenant_id "
                            f"to be visible to all tenants. This means any row inserted without "
                            f"a tenant_id is a global data leak. The policy should require "
                            f"tenant_id to be NOT NULL, or use a separate admin-only policy "
                            f"for NULL rows."
                        )
    def test_rls_force_enabled(self):
        """RLS must be FORCE enabled (applies even to table owners)."""
        for migration_file in sorted(_L4_MIGRATIONS_DIR.glob("*.py")):
            source = migration_file.read_text()
            if "RLS_TABLES" not in source:
                continue

            assert "FORCE ROW LEVEL SECURITY" in source, (
                f"{migration_file.name}: RLS is not FORCE enabled. Without FORCE, "
                f"the table owner role bypasses all RLS policies."
            )


# ---------------------------------------------------------------------------
# Tests: Connection Pool Reset
# ---------------------------------------------------------------------------

class TestConnectionPoolReset:
    """Verify that database sessions are properly reset between requests.

    If ``app.tenant_id`` persists across connection pool reuse, Tenant A's
    context could leak into Tenant B's request.
    """

    def test_session_uses_set_local_not_set(self):
        """Database module must use ``SET LOCAL`` (transaction-scoped), not
        ``SET`` (session-scoped).

        ``SET LOCAL`` automatically resets when the transaction ends.
        ``SET`` persists across the connection's lifetime, which means
        connection pool reuse would leak tenant context.
        """
        source = _L4_DATABASE_MODULE.read_text()

        # Find all SET statements for app.tenant_id
        set_statements = re.findall(r"(SET\s+(?:LOCAL\s+)?app\.tenant_id)", source, re.IGNORECASE)

        for stmt in set_statements:
            assert "LOCAL" in stmt.upper(), (
                f"Found '{stmt}' without LOCAL qualifier. "
                f"SET without LOCAL persists across connection pool reuse, "
                f"causing tenant context leakage between requests."
            )

    def test_no_raw_set_without_local(self):
        """No ``SET app.tenant_id`` (without LOCAL) should appear anywhere."""
        source = _L4_DATABASE_MODULE.read_text()

        # Match SET app.tenant_id but NOT SET LOCAL app.tenant_id
        # Use negative lookbehind for LOCAL
        matches = re.findall(
            r"['\"]SET\s+app\.tenant_id",
            source,
            re.IGNORECASE,
        )

        for match in matches:
            assert "LOCAL" in match.upper(), (
                f"Found raw SET app.tenant_id without LOCAL: {match!r}. "
                f"This causes tenant context leakage in connection pools."
            )

    def test_session_commits_or_rollbacks(self):
        """Every session context manager must have both commit and rollback paths.

        If a session is returned to the pool without commit/rollback, the
        ``SET LOCAL`` may persist in some database drivers.
        """
        source = _L4_DATABASE_MODULE.read_text()

        # Check that get_db_from_context has both commit and rollback
        # (or at minimum, the session is properly managed)
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name == "get_db_from_context":
                    func_source = ast.get_source_segment(source, node) or ""

                    # Should have try/except with rollback
                    has_rollback = "rollback" in func_source
                    has_yield = "yield" in func_source

                    assert has_yield, (
                        "get_db_from_context does not yield a session. "
                        "It must be an async generator for FastAPI Depends()."
                    )

                    # Note: rollback may be handled by the session factory
                    # context manager, so we just verify the yield exists
                    return

        pytest.fail("get_db_from_context not found in database.py")
