"""Bulk-fix old import paths across the test suite."""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).parent.resolve()
TESTS_DIR = REPO_ROOT / "tests"
SERVICES_DIR = REPO_ROOT / "services"

def fix_file(path: Path) -> bool:
    """Fix imports in a single file. Return True if changed."""
    original = path.read_text(encoding="utf-8")
    text = original

    # Pattern 1: from shared.XXX → from value_fabric.shared.XXX
    # Only match at start of line (after optional whitespace)
    text = re.sub(r"^(\s*)from shared\.([\w.]+) import", r"\1from value_fabric.shared.\2 import", text, flags=re.MULTILINE)
    text = re.sub(r"^(\s*)import shared\b", r"\1import value_fabric.shared", text, flags=re.MULTILINE)

    # Pattern 2: old long-form value_fabric.layerX_*.src. → value_fabric.layerX.
    text = re.sub(r"\bvalue_fabric\.layer1_ingestion\.src\.", "value_fabric.layer1.", text)
    text = re.sub(r"\bvalue_fabric\.layer2_extraction\.src\.", "value_fabric.layer2.", text)
    text = re.sub(r"\bvalue_fabric\.layer3_knowledge\.src\.", "value_fabric.layer3.", text)
    text = re.sub(r"\bvalue_fabric\.layer4_agents\.src\.", "value_fabric.layer4.", text)
    text = re.sub(r"\bvalue_fabric\.layer5_ground_truth\.src\.layer5_ground_truth\.", "value_fabric.layer5.", text)
    text = re.sub(r"\bvalue_fabric\.layer5_ground_truth\.src\.", "value_fabric.layer5.", text)
    text = re.sub(r"\bvalue_fabric\.layer6_benchmarks\.src\.", "value_fabric.layer6.", text)

    # Pattern 3: from identity.XXX → from value_fabric.shared.identity.XXX
    text = re.sub(r"^(\s*)from identity\.([\w.]+) import", r"\1from value_fabric.shared.identity.\2 import", text, flags=re.MULTILINE)

    if text != original:
        path.write_text(text, encoding="utf-8")
        return True
    return False


def main():
    changed = []
    for path in TESTS_DIR.rglob("*.py"):
        if fix_file(path):
            changed.append(path.relative_to(REPO_ROOT))

    # Also fix service test directories
    for svc_tests in SERVICES_DIR.rglob("tests/*.py"):
        if fix_file(svc_tests):
            changed.append(svc_tests.relative_to(REPO_ROOT))
    for svc_tests in SERVICES_DIR.rglob("tests/**/*.py"):
        if fix_file(svc_tests):
            changed.append(svc_tests.relative_to(REPO_ROOT))

    # Fix conftest files
    for conftest in TESTS_DIR.rglob("conftest.py"):
        if fix_file(conftest):
            changed.append(conftest.relative_to(REPO_ROOT))
    for conftest in SERVICES_DIR.rglob("tests/conftest.py"):
        if fix_file(conftest):
            changed.append(conftest.relative_to(REPO_ROOT))

    print(f"Changed {len(changed)} files:")
    for p in sorted(changed):
        print(f"  {p}")


if __name__ == "__main__":
    main()
