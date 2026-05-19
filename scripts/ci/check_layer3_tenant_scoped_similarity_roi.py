from __future__ import annotations

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
# value_fabric/layer3 is a path-redirect shim; canonical source lives under
# services/layer3-knowledge/src/ (ADR-027).
FILES = [
    ROOT / 'services/layer3-knowledge/src/analytics/similarity.py',
    ROOT / 'services/layer3-knowledge/src/agents/roi_calculation.py',
]
ALLOW_MARKER = 'strict-scoped-query-execution'


def main() -> int:
    errors: list[str] = []
    for file in FILES:
        text = file.read_text(encoding='utf-8')
        for m in re.finditer(r'MATCH \(', text):
            start = max(0, m.start() - 180)
            context = text[start:m.start()]
            if ALLOW_MARKER not in context:
                line = text[:m.start()].count('\n') + 1
                errors.append(f"{file.relative_to(ROOT)}:{line} contains raw MATCH ( without tenant-scoped wrapper marker")
    if errors:
        print('\n'.join(errors))
        return 1
    print('OK: Layer3 similarity/ROI modules only use tenant-scoped query wrappers.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
