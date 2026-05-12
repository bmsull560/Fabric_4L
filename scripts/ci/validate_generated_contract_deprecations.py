#!/usr/bin/env python3
from __future__ import annotations
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
META_PATH = ROOT / 'contracts' / 'deprecations' / 'generated-contract-deprecations.json'
OPENAPI_DIR = ROOT / 'contracts' / 'openapi'
TS_GEN_DIR = ROOT / 'packages' / 'platform-contract' / 'src' / 'typescript' / 'generated'
PY_FILES = [
    ROOT / 'value_fabric' / 'layer3' / 'api' / 'models.py',
    ROOT / 'services' / 'layer3-knowledge' / 'src' / 'api' / 'models.py',
]


def parse_v(v: str) -> tuple[int, ...]:
    nums = re.findall(r'\d+', v)
    return tuple(int(n) for n in nums) if nums else (0,)


def openapi_deprecated_fields(spec: dict) -> set[str]:
    out = set()
    comps = spec.get('components', {}).get('schemas', {})
    for sname, schema in comps.items():
        for pname, pdef in schema.get('properties', {}).items():
            if isinstance(pdef, dict) and pdef.get('deprecated') is True:
                out.add(f"components.schemas.{sname}.properties.{pname}")
    return out


def main() -> int:
    if not META_PATH.exists():
        print(f"::error::Missing metadata file: {META_PATH}")
        return 1

    metadata = json.loads(META_PATH.read_text())
    current_version = metadata.get('current_contract_version', '0.0')
    current_t = parse_v(current_version)
    entries = metadata.get('entries', [])
    by_key = {e['key']: e for e in entries}

    errors: list[str] = []
    warnings: list[str] = []

    discovered: set[str] = set()
    for spec_path in sorted(OPENAPI_DIR.glob('*.json')):
        spec = json.loads(spec_path.read_text())
        fields = openapi_deprecated_fields(spec)
        for f in fields:
            discovered.add(f"{spec_path.name}:{f}")

    for key in sorted(discovered):
        if key not in by_key:
            errors.append(f"Missing deprecation metadata for {key}")
            continue
        meta = by_key[key]
        for req in ('introduced_in', 'removal_target', 'replacement_field'):
            if not meta.get(req):
                errors.append(f"{key} missing required metadata '{req}'")
        if parse_v(meta.get('removal_target', '0.0')) <= current_t:
            approved_until = meta.get('exception_approved_until')
            if approved_until and parse_v(approved_until) > current_t:
                warnings.append(f"{key} past removal target but exception approved through {approved_until}")
            else:
                errors.append(f"{key} exceeded removal target {meta.get('removal_target')} (current {current_version})")

    # Artifact parity checks
    for key in sorted(discovered):
        spec_name, path_key = key.split(':', 1)
        field = path_key.rsplit('.', 1)[-1]
        ts_file = TS_GEN_DIR / spec_name.replace('.json', '').replace('-', '_')
        ts_path = ts_file.with_suffix('.ts')
        if not ts_path.exists():
            errors.append(f"Missing generated TS artifact for {spec_name}: expected {ts_path}")
            continue
        ts_text = ts_path.read_text()
        if f"{field}:" not in ts_text:
            errors.append(f"TS artifact missing deprecated field '{field}' from {key}")
        if '@deprecated' not in ts_text:
            errors.append(f"TS artifact missing @deprecated annotations for {spec_name}")

    py_texts = [p.read_text() for p in PY_FILES if p.exists()]
    for key in sorted(discovered):
        field = key.rsplit('.', 1)[-1]
        if not any((field in t and 'deprecated' in t.lower()) for t in py_texts):
            warnings.append(f"Python outputs do not clearly carry deprecated note for field '{field}'")

    for w in warnings:
        print(f"::warning::{w}")
    for e in errors:
        print(f"::error::{e}")

    if errors:
        print(f"Validation failed with {len(errors)} error(s)")
        return 1

    print(f"Validated {len(discovered)} deprecated OpenAPI fields against metadata and generated artifacts")
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
