import subprocess
import sys
import re

IGNORE_FILES = [
    "services/layer3-knowledge/tests/test_api_wrapper_startup_regression.py",
    "services/layer3-knowledge/tests/test_benchmark_policies_route.py",
    "services/layer3-knowledge/tests/test_graph_alias_deprecation_policy.py",
    "services/layer4-agents/tests/test_accounts_api.py",
    "services/layer4-agents/tests/test_billing_service.py",
    "services/layer4-agents/tests/test_case_permissions_and_audit.py",
    "services/layer4-agents/tests/test_checkpoints_route_errors.py",
    "services/layer4-agents/tests/test_crm_sync_service.py",
    "services/layer4-agents/tests/test_feature_flags.py",
    "services/layer4-agents/tests/test_frontend_endpoint_contracts.py",
    "services/layer4-agents/tests/test_governance_workflow_contracts.py",
    "services/layer4-agents/tests/test_observability_contract_integration.py",
    "services/layer4-agents/tests/test_oidc_id_token_validation.py",
    "services/layer4-agents/tests/test_startup_contract.py",
    "services/layer4-agents/tests/test_workflow_replay_determinism.py",
    "tests/ci/test_check_no_nul_bytes.py",
    "tests/ci/test_deprecated_namespace_imports.py",
    "tests/contract/test_entity_contract.py",
    "tests/contract/test_l3_provenance_audit_contract.py",
    "tests/contract/test_l3_route_alias_parity.py",
    "tests/contract/test_l3_route_contract_regression.py",
    "tests/contract/test_layer3_compat_metrics.py",
    "tests/contract/test_layer3_graph_deprecation_contract.py",
    "tests/contract/test_state_inspector_auth_contract.py",
    "tests/contract/test_system_route_contract.py",
    "tests/layer3/test_model_registry_tenant_context.py",
    "tests/release/test_platform_contract_deprecations.py",
    "tests/security/test_auth_rate_limiting.py",
    "tests/security/test_auth_session_hijacking.py",
    "tests/security/test_csrf_comprehensive.py",
    "tests/test_cross_tenant_hostile.py",
    "tests/test_model_registry_integration.py",
]

def run_pytest(label, extra_args=None):
    print(f"\n{'='*60}")
    print(f"Running: {label}")
    print(f"{'='*60}")
    
    cmd = [sys.executable, "-m", "pytest", "--strict-markers", "--continue-on-collection-errors", "--timeout=10", "-q", "--no-header"]
    if extra_args:
        cmd.extend(extra_args)
    for f in IGNORE_FILES:
        cmd.extend(["--ignore", f])
    
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    
    lines = (result.stdout + result.stderr).splitlines()
    for line in lines[-30:]:
        print(line)
    
    summary = {}
    for line in lines:
        m = re.search(r'(\d+) passed', line)
        if m: summary['passed'] = int(m.group(1))
        m = re.search(r'(\d+) failed', line)
        if m: summary['failed'] = int(m.group(1))
        m = re.search(r'(\d+) error', line)
        if m: summary['errors'] = int(m.group(1))
        m = re.search(r'(\d+) skipped', line)
        if m: summary['skipped'] = int(m.group(1))
        m = re.search(r'(\d+) deselected', line)
        if m: summary['deselected'] = int(m.group(1))
    
    print(f"\nParsed: {summary}")
    print(f"Exit code: {result.returncode}")
    return summary, result.returncode, lines

# Run 1: all tests we can collect and execute
summary1, code1, lines1 = run_pytest("All runnable tests")

# Run 2: unit tests only
summary2, code2, lines2 = run_pytest("Unit tests", ["-m", "unit"])

print("\nDone.")
