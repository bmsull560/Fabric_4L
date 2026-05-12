"""CI guardrail for tenant isolation in Layer 6 benchmark dataset queries."""

from pathlib import Path
import re


REPO_ROOT = Path(__file__).resolve().parents[2]
LAYER6_REPOSITORY_PATHS = [
    REPO_ROOT / "value_fabric/layer6/repositories",
    REPO_ROOT / "services/layer6-benchmarks/src/repositories",
]
BENCHMARK_DATASET_MATCH = re.compile(r"MATCH\s*\(d:BenchmarkDataset\)")
TENANT_PREDICATE = re.compile(r"d\.tenant_id\s*=\s*\$tenant_id")


def test_benchmarkdataset_match_always_scopes_tenant() -> None:
    violations: list[str] = []
    for repo_path in LAYER6_REPOSITORY_PATHS:
        for py_file in repo_path.rglob("*.py"):
            text = py_file.read_text(encoding="utf-8")
            for match in BENCHMARK_DATASET_MATCH.finditer(text):
                snippet = text[match.start() : match.start() + 240]
                if not TENANT_PREDICATE.search(snippet):
                    violations.append(
                        f"{py_file.relative_to(REPO_ROOT)} missing tenant predicate near: "
                        f"{snippet.splitlines()[0].strip()}"
                    )

    assert not violations, "Layer 6 tenant-isolation query violations:\n" + "\n".join(violations)
