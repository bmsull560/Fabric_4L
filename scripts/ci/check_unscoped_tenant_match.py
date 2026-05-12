#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
import warnings
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from value_fabric.shared.identity.isolation import DEFAULT_TENANT_LABEL_POLICY

SCAN_ROOTS = [ROOT / "services" / "layer3-knowledge" / "src" / "services"]
BASELINE = ROOT / "scripts" / "ci" / "layer3_unscoped_match_baseline.txt"
PATTERN = re.compile(r"MATCH\s*\(\s*\w+\s*:\s*(?P<label>[A-Za-z_][A-Za-z0-9_]*)\s*(?:\{(?P<props>[^}]*)\})?", re.IGNORECASE)


def main() -> int:
    warnings.filterwarnings("ignore", category=UserWarning)
    failures: list[str] = []
    tenant_labels = DEFAULT_TENANT_LABEL_POLICY.tenant_labels
    for scan_root in SCAN_ROOTS:
        for path in scan_root.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            for idx, line in enumerate(text.splitlines(), start=1):
                m = PATTERN.search(line)
                if not m:
                    continue
                label = m.group("label")
                props = (m.group("props") or "")
                same_line_tenant_where = "WHERE" in line.upper() and ("tenant_id" in line or "tenantId" in line)
                if label in tenant_labels and "tenant_id" not in props and "tenantId" not in props and not same_line_tenant_where:
                    failures.append(f"{path.relative_to(ROOT)}:{idx}: MATCH on tenant-owned label '{label}' missing tenant_id property")

    current = sorted(failures)
    baseline = sorted([line.strip() for line in BASELINE.read_text(encoding="utf-8").splitlines() if line.strip()])
    introduced = [entry for entry in current if entry not in baseline]
    resolved = [entry for entry in baseline if entry not in current]
    if introduced or resolved:
        print("Tenant MATCH lint drift detected.")
        if introduced:
            print("Introduced violations:")
            for failure in introduced:
                print(f"- {failure}")
        if resolved:
            print("Resolved violations (refresh baseline if intentional):")
            for failure in resolved:
                print(f"- {failure}")
        return 1

    print(f"Tenant MATCH lint baseline stable ({len(current)} tracked violation(s)).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
