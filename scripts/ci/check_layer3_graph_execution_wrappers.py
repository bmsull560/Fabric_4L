#!/usr/bin/env python3
from __future__ import annotations
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
TARGET=ROOT/'value_fabric'/'layer3'
PATTERN=re.compile(r"\b(session\.run|execute_query)\s*\(")

ALLOWED_FILE_FRAGMENTS=(
    '/backup/', '/migrations/', '/schema/', 'security/query_validator.py', 'db/tenant_queries.py', 'db/driver.py'
)
APPROVED_MARKERS=(
    'TenantQueryExecutor.run', '_run_scoped', 'TenantScopedCypher', 'ScopedQuery', 'tenant_id', 'allow_system_query=True'
)

errors=[]
baseline_path = ROOT / 'scripts' / 'ci' / 'layer3_graph_execution_wrapper_baseline.txt'
baseline = set()
if baseline_path.exists():
    baseline = {line.strip() for line in baseline_path.read_text(encoding='utf-8').splitlines() if line.strip()}

for path in sorted(TARGET.rglob('*.py')):
    rel='/' + str(path.relative_to(ROOT)).replace('\\','/')
    if any(x in rel for x in ALLOWED_FILE_FRAGMENTS):
        continue
    text=path.read_text(encoding='utf-8',errors='ignore').splitlines()
    for i,line in enumerate(text,1):
        if not PATTERN.search(line):
            continue
        win='\n'.join(text[max(0,i-8):min(len(text),i+8)])
        if any(m in win for m in APPROVED_MARKERS):
            continue
        location = f"{path.relative_to(ROOT)}:{i}"
        if location in baseline:
            continue
        errors.append(f"{location}: raw graph execution call without approved scoped wrapper marker")

if errors:
    print('Layer3 graph wrapper check failed:')
    for e in errors:
        print(' -',e)
    raise SystemExit(1)
print('Layer3 graph wrapper check passed')
