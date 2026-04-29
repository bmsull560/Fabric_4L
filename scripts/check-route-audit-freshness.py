#!/usr/bin/env python3
import json
import re
import sys
from pathlib import Path

app = Path('frontend/client/src/App.tsx')
route_map = Path('frontend/audit-output/route-map.md')
extraction = Path('frontend/audit-output/track-a-route-extraction.json')

missing = [str(p) for p in (app, route_map, extraction) if not p.exists()]
if missing:
    print(f"ERROR: missing required files: {', '.join(missing)}")
    sys.exit(1)

if route_map.stat().st_mtime < app.stat().st_mtime:
    print('ERROR: frontend/audit-output/route-map.md is older than frontend/client/src/App.tsx')
    sys.exit(1)

summary = json.loads(extraction.read_text()).get('summary', {})
expected_total = summary.get('total')
if not isinstance(expected_total, int):
    print('ERROR: track-a-route-extraction.json missing numeric summary.total')
    sys.exit(1)

match = re.search(r"\*\*Total Routes:\*\*\s*(\d+)", route_map.read_text())
if not match:
    print('ERROR: route-map.md missing "**Total Routes:** <count>" header')
    sys.exit(1)

found_total = int(match.group(1))
if found_total != expected_total:
    print(f'ERROR: route count drift detected: route-map={found_total}, extraction={expected_total}')
    sys.exit(1)

print(f'OK: route-map freshness and count checks passed (total routes: {expected_total})')
