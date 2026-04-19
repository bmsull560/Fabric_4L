#!/usr/bin/env python3
"""Fix incorrect test imports in layer4-agents tests."""

import ast
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

PATTERNS = [
    # Standard pattern: value_fabric.layer4_agents.src.X -> src.X
    (r'from value_fabric\.layer4_agents\.src\.([\w.]+) import', r'from src.\1 import'),
    # Pattern without src: value_fabric.layer4_agents.models -> src.models
    (r'from value_fabric\.layer4_agents\.([\w.]+) import', r'from src.\1 import'),
]

def fix_file(filepath: Path) -> int:
    """Fix imports in a single file. Returns count of replacements."""
    if not filepath.exists():
        print(f"  SKIP: {filepath} (not found)")
        return 0

    content = filepath.read_text()

    # Pre-validate: check for syntax errors
    try:
        ast.parse(content)
    except SyntaxError as e:
        print(f"  SYNTAX ERROR in {filepath}: {e}")
        # Still attempt fixes even with syntax errors

    # Apply all patterns
    total_count = 0
    new_content = content
    for pattern, replacement in PATTERNS:
        new_content, count = re.subn(pattern, replacement, new_content)
        total_count += count

    # Fix broken imports like "from mrt X" or "from import X"
    new_content, count = re.subn(
        r'from\s+\w+\s+([A-Z][\w]*)\n',
        lambda m: f'from src.models.tool_schemas import {m.group(1)}\n',
        new_content
    )
    total_count += count

    new_content, count = re.subn(
        r'from\s+import\s+(\w+)',
        r'from src.tools.generation_tools import \1',
        new_content
    )
    total_count += count

    if total_count > 0:
        filepath.write_text(new_content)
        print(f"  FIXED: {filepath} ({total_count} replacements)")
    else:
        print(f"  OK: {filepath} (no changes needed)")

    return total_count

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
