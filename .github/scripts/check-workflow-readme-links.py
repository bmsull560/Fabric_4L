#!/usr/bin/env python3
"""Fail if .github/workflows/README.md references workflow files that do not exist."""
from __future__ import annotations

import re
from pathlib import Path
import sys

repo = Path(__file__).resolve().parents[2]
readme = repo / '.github/workflows/README.md'
workflows_dir = repo / '.github/workflows'

text = readme.read_text(encoding='utf-8')
# Capture inline-code references like `foo.yml`
referenced = sorted(set(re.findall(r'`([A-Za-z0-9_.-]+\.ya?ml)`', text)))
existing = {p.name for p in workflows_dir.glob('*.yml')} | {p.name for p in workflows_dir.glob('*.yaml')}

missing = [name for name in referenced if name not in existing]
if missing:
    print('❌ README references workflow files that do not exist:')
    for name in missing:
        print(f'  - {name}')
    print('\nUpdate .github/workflows/README.md to match current filenames.')
    sys.exit(1)

print(f'✅ README workflow references are valid ({len(referenced)} references checked).')
