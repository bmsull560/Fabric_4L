"""Root conftest.py for Fabric 4L monorepo.

Ensures sys.path is set up before pytest imports any test modules.
Only adds the shared package path. Layer test directories are expected
to add their own src paths in their local conftest.py files.

Also enforces mandatory test dependencies at collection time so that
missing packages produce an immediate, actionable error rather than
silently skipping tests.
"""

import importlib.util
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.resolve()

# Shared package (canonical location)
_SHARED_SRC = _REPO_ROOT / "packages" / "shared" / "src"
if _SHARED_SRC.exists() and str(_SHARED_SRC) not in sys.path:
    sys.path.insert(0, str(_SHARED_SRC))


# ---------------------------------------------------------------------------
# Mandatory dependency enforcement
#
# These packages must be present for the mandatory test profile to run.
# They are listed in each service's [project.optional-dependencies.dev].
# A missing package here means the dev environment was not set up correctly.
#
# Optional/slow deps (playwright, pymupdf4llm) are NOT listed here — their
# test files use pytest.mark.skipif so they are collected but skipped cleanly.
# ---------------------------------------------------------------------------

# Maps import name → install instruction
_MANDATORY_DEPS: dict[str, str] = {
    # Layer 1 — HTTP mocking
    "respx": "pip install 'respx>=0.21'  (layer1-ingestion[dev] or tests/requirements-test.txt)",
    # Layer 1 — content extraction (already a production dep)
    "trafilatura": "pip install 'trafilatura>=1.6'  (layer1-ingestion dependency)",
    # Layer 1 — XXE-safe XML (already a production dep)
    "defusedxml": "pip install 'defusedxml>=0.7'  (layer1-ingestion dependency)",
    # Layer 4 — PostgreSQL driver for testcontainers integration tests
    "psycopg": "pip install 'psycopg[binary]>=3.1'  (layer4-agents[dev])",
    # Layer 4 — pydantic email validation
    "email_validator": "pip install 'email-validator>=2.1'  (layer4-agents[dev])",
    # Shared identity — JWT library (already a production dep in layer4)
    "jose": "pip install 'python-jose[cryptography]>=3.3'  (layer4-agents dependency)",
}


def pytest_configure(config) -> None:
    """Fail fast when mandatory test dependencies are missing.

    Runs before collection so the error is immediate and unambiguous,
    rather than surfacing as a cryptic ImportError mid-collection.

    Pass --no-mandatory-dep-check to skip this check (e.g. for dry-run
    collection audits from a clean checkout).
    """
    if getattr(config.option, "no_mandatory_dep_check", False):
        return

    missing = [
        (name, hint)
        for name, hint in _MANDATORY_DEPS.items()
        if importlib.util.find_spec(name) is None
    ]

    if not missing:
        return

    lines = ["", "Mandatory test dependencies are missing.", ""]
    for name, hint in missing:
        lines.append(f"  \u2717 {name}")
        lines.append(f"    \u2192 {hint}")
    lines += [
        "",
        "Install all mandatory deps for the full mandatory profile:",
        "  pip install -r tests/requirements-test.txt",
        "",
        "To skip this check (e.g. for a dry-run collection audit):",
        "  pytest --no-mandatory-dep-check --collect-only",
        "",
    ]
    raise SystemExit("\n".join(lines))


def pytest_addoption(parser) -> None:
    """Add --no-mandatory-dep-check flag for lightweight collection runs."""
    parser.addoption(
        "--no-mandatory-dep-check",
        action="store_true",
        default=False,
        dest="no_mandatory_dep_check",
        help="Skip mandatory dependency enforcement (for --collect-only dry runs).",
    )


def pytest_collection_modifyitems(config, items) -> None:
    """Automatically mark tests as mandatory based on their other markers.

    Tests marked with: unit, contract, security, or tenant_boundary
    are automatically considered mandatory unless they also have:
    - slow
    - requires_postgres
    - requires_redis
    - requires_neo4j
    - requires_openai
    - e2e
    - integration
    - performance

    This allows selecting mandatory tests with: pytest -m mandatory
    """
    mandatory_markers = {"unit", "contract", "security", "tenant_boundary"}
    exclusion_markers = {
        "slow", "requires_postgres", "requires_redis", "requires_neo4j",
        "requires_openai", "e2e", "integration", "performance", "flaky", "quarantine"
    }

    for item in items:
        item_markers = {m.name for m in item.iter_markers()}

        # Skip if already has mandatory marker
        if "mandatory" in item_markers:
            continue

        # Skip if has any exclusion marker
        if item_markers & exclusion_markers:
            continue

        # Mark as mandatory if it has any mandatory marker
        if item_markers & mandatory_markers:
            item.add_marker("mandatory")
