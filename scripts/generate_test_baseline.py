import subprocess
import sys
import re
import json
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.resolve()

def run_pytest(target, label, timeout=10):
    """Run pytest on a specific target and return parsed results."""
    print(f"\n{'='*60}")
    print(f"Running: {label}")
    print(f"Target: {target}")
    print(f"{'='*60}")
    
    cmd = [
        sys.executable, "-m", "pytest",
        str(target),
        "-v",
        f"--timeout={timeout}",
        "--continue-on-collection-errors",
        "--no-header"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    
    # Parse results
    passed = failed = errors = skipped = 0
    for line in result.stdout.splitlines() + result.stderr.splitlines():
        m = re.search(r'(\d+) passed', line)
        if m: passed = int(m.group(1))
        m = re.search(r'(\d+) failed', line)
        if m: failed = int(m.group(1))
        m = re.search(r'(\d+) error', line)
        if m: errors = int(m.group(1))
        m = re.search(r'(\d+) skipped', line)
        if m: skipped = int(m.group(1))
    
    print(f"Result: {passed} passed, {failed} failed, {errors} errors, {skipped} skipped (exit={result.returncode})")
    
    return {
        "label": label,
        "target": str(target),
        "passed": passed,
        "failed": failed,
        "errors": errors,
        "skipped": skipped,
        "exit_code": result.returncode,
        "output_tail": "\n".join((result.stdout + result.stderr).splitlines()[-20:])
    }

# Define test targets to sample
targets = [
    ("services/layer1-ingestion/tests/unit/test_models.py", "L1 Unit - Models"),
    ("services/layer1-ingestion/tests/unit/test_crawler_config.py", "L1 Unit - Crawler Config"),
    ("services/layer1-ingestion/tests/unit/test_scheduler.py", "L1 Unit - Scheduler"),
    ("services/layer1-ingestion/tests/unit/test_adapters.py", "L1 Unit - Adapters"),
    ("services/layer2-extraction/tests/test_deduplicator.py", "L2 Unit - Deduplicator"),
    ("services/layer2-extraction/tests/test_chunker.py", "L2 Unit - Chunker"),
    ("services/layer3-knowledge/tests/unit/test_graph_queries.py", "L3 Unit - Graph Queries"),
    ("services/layer4-agents/tests/unit/test_rate_limiting.py", "L4 Unit - Rate Limiting"),
    ("services/layer5-ground-truth/tests/unit/test_label_validation.py", "L5 Unit - Label Validation"),
    ("services/layer6-benchmarks/tests/unit/test_api_wrapper.py", "L6 Unit - API Wrapper"),
    ("tests/arch/test_tenant_architecture.py", "Arch - Tenant Architecture"),
    ("tests/arch/test_testability_architecture.py", "Arch - Testability"),
    ("tests/security/test_tenant_isolation.py", "Security - Tenant Isolation"),
    ("tests/security/test_injection.py", "Security - Injection"),
    ("tests/contract/test_l2_l3_contract.py", "Contract - L2-L3"),
    ("tests/contract/test_l3_graph_contract.py", "Contract - L3 Graph"),
]

results = []
for target, label in targets:
    target_path = REPO_ROOT / target
    if target_path.exists():
        result = run_pytest(target_path, label)
        results.append(result)
    else:
        print(f"SKIP: {target} not found")
        results.append({
            "label": label,
            "target": str(target),
            "passed": 0, "failed": 0, "errors": 0, "skipped": 0,
            "exit_code": -1,
            "output_tail": "File not found"
        })

# Save report
report_path = REPO_ROOT / "TEST_BASELINE_REPORT.json"
with open(report_path, "w") as f:
    json.dump(results, f, indent=2)

print(f"\n{'='*60}")
print("BASELINE SAMPLING COMPLETE")
print(f"{'='*60}")
total_passed = sum(r["passed"] for r in results)
total_failed = sum(r["failed"] for r in results)
total_errors = sum(r["errors"] for r in results)
total_skipped = sum(r["skipped"] for r in results)
print(f"Total sampled: {len(results)} targets")
print(f"Total passed: {total_passed}")
print(f"Total failed: {total_failed}")
print(f"Total errors: {total_errors}")
print(f"Total skipped: {total_skipped}")
print(f"Report saved to: {report_path}")
