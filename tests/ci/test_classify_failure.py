from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "ci" / "classify_failure.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("classify_failure", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_classifier_detects_taxonomy_categories() -> None:
    module = _load_module()
    classifier = module.FailureClassifier()
    cases = {
        "AssertionError: expected 1 but got 2": "TEST_EXPECTATION_DRIFT",
        "ModuleNotFoundError: No module named 'value_fabric.shared.identity'": "SOURCE_PATH_DRIFT",
        "FixtureLookupError: fixture auth_client not found": "FIXTURE_SETUP_PORTABILITY",
        "vi.useFakeTimers left window.location mock not restored": "TEST_ISOLATION_LEAK",
        "tenant_id mismatch caused cross-tenant access in RLS policy": "REAL_SECURITY_REGRESSION",
        "OIDC credentials not configured for billing sandbox": "ENVIRONMENT_DEPENDENCY",
        "Timeout: test timed out after 30000ms": "TIMEOUT",
        "OpenAPI contract drift: response shape required field missing": "CONTRACT_BOUNDARY_DRIFT",
    }

    for output, expected in cases.items():
        assert classifier.classify(output).category_key == expected


def test_security_environment_timeout_and_unknown_are_not_auto_fixable() -> None:
    module = _load_module()
    classifier = module.FailureClassifier()
    for output in (
        "tenant isolation failed for JWT auth",
        "missing secret for external service",
        "operation timed out after 60s",
        "unclassified opaque failure text",
    ):
        result = classifier.classify(output)
        assert result.auto_fixable is False


def test_cli_outputs_stable_json_and_blocks_on_blocker(tmp_path: Path) -> None:
    log = tmp_path / "failure.log"
    log.write_text("ModuleNotFoundError: No module named 'legacy.path'\n", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--file", str(log), "--format", "json"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 2
    payload = json.loads(result.stdout)
    assert payload[0]["category_key"] == "SOURCE_PATH_DRIFT"
    assert payload[0]["blocks_ga"] is True
    assert payload[0]["fix_strategy"] == "update_import_paths"


def test_cli_non_blocker_returns_zero(tmp_path: Path) -> None:
    log = tmp_path / "failure.log"
    log.write_text("AssertionError: expected true but received false\n", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--file", str(log), "--format", "markdown"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert "TEST_EXPECTATION_DRIFT" in result.stdout
