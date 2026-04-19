#!/usr/bin/env python3
"""Fix incorrect test imports in layer4-agents tests."""

import re
from pathlib import Path

# List of test files with incorrect imports
TEST_FILES = [
    "value-fabric/layer4-agents/tests/test_workflows_real_execution.py",
    "value-fabric/layer4-agents/tests/test_websocket_manager.py",
    "value-fabric/layer4-agents/tests/test_tenant_rate_limits.py",
    "value-fabric/layer4-agents/tests/test_pack_variable_loader.py",
    "value-fabric/layer4-agents/tests/test_notification.py",
    "value-fabric/layer4-agents/tests/test_model_registry.py",
    "value-fabric/layer4-agents/tests/test_llm_cost_tracking.py",
    "value-fabric/layer4-agents/tests/test_llm_cost_metrics.py",
    "value-fabric/layer4-agents/tests/test_llm_budget_guardrails.py",
    "value-fabric/layer4-agents/tests/test_interfaces_exports.py",
    "value-fabric/layer4-agents/tests/test_integration_service.py",
    "value-fabric/layer4-agents/tests/test_health_tracker.py",
    "value-fabric/layer4-agents/tests/test_feature_flags.py",
    "value-fabric/layer4-agents/tests/test_crm_sync_service.py",
    "value-fabric/layer4-agents/tests/test_checkpoint_boundary.py",
    "value-fabric/layer4-agents/tests/test_c1_proxy.py",
    "value-fabric/layer4-agents/tests/test_billing_service.py",
    "value-fabric/layer4-agents/tests/test_accounts_api.py",
]

PATTERN = r'from value_fabric\.layer4_agents\.src\.([\w.]+) import'
REPLACEMENT = r'from src.\1 import'

def fix_file(filepath: Path) -> int:
    """Fix imports in a single file. Returns count of replacements."""
    if not filepath.exists():
        print(f"  SKIP: {filepath} (not found)")
        return 0
    
    content = filepath.read_text()
    new_content, count = re.subn(PATTERN, REPLACEMENT, content)
    
    if count > 0:
        filepath.write_text(new_content)
        print(f"  FIXED: {filepath} ({count} replacements)")
    else:
        print(f"  OK: {filepath} (no changes needed)")
    
    return count

def main():
    root = Path("C:/Users/BBB/Fabric_4L")
    total = 0
    
    print("Fixing test imports...")
    for rel_path in TEST_FILES:
        filepath = root / rel_path
        total += fix_file(filepath)
    
    print(f"\nDone! Total replacements: {total}")

if __name__ == "__main__":
    main()
