#!/usr/bin/env python3
"""
OpenAPI Analysis Script for Tri-Track Audit (Track B)
Parses OpenAPI specs and cross-references with frontend hook usage.
Identifies orphan endpoints (backend endpoints with no frontend surface).
"""

import json
import re
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Set

@dataclass
class EndpointInfo:
    layer: str
    path: str
    method: str
    operation_id: str
    tags: List[str]
    summary: str
    has_hook: bool
    hook_name: Optional[str]
    has_component_surface: bool
    component: Optional[str]
    status: str  # 'CONNECTED', 'ORPHAN', 'SURFACE_GAP', 'TYPE_GAP'

# Load hook analysis to get known endpoints
hook_analysis_path = Path("audit-output/track-a-hook-analysis.json")
hook_data = json.loads(hook_analysis_path.read_text(encoding='utf-8'))

# Build set of consumed endpoints
consumed_endpoints: Set[str] = set()
hook_mapping: Dict[str, str] = {}

for hook in hook_data['hooks']:
    hook_name = hook['name']
    for endpoint in hook.get('api_endpoints', []):
        # Normalize endpoint for matching
        parts = endpoint.split(' ', 1)
        if len(parts) == 2:
            method, path = parts
            # Remove query params and normalize
            path = path.split('?')[0]
            key = f"{method}:{path}"
            consumed_endpoints.add(key)
            hook_mapping[key] = hook_name

print(f"Found {len(consumed_endpoints)} consumed endpoints from hooks")

# Load OpenAPI specs
openapi_dir = Path("contracts/openapi")
openapi_files = list(openapi_dir.glob("*.json"))

print(f"\nAnalyzing {len(openapi_files)} OpenAPI spec files...")

all_endpoints = []

for spec_file in sorted(openapi_files):
    layer = spec_file.stem  # e.g., 'layer3-knowledge'
    spec = json.loads(spec_file.read_text(encoding='utf-8'))
    
    paths = spec.get('paths', {})
    
    for path, methods in paths.items():
        for method, operation in methods.items():
            if method in ['get', 'post', 'put', 'patch', 'delete']:
                operation_id = operation.get('operationId', 'unknown')
                tags = operation.get('tags', [])
                summary = operation.get('summary', '')
                
                # Check if consumed
                norm_method = method.upper()
                # Handle path params
                norm_path = re.sub(r'\{([^}]+)\}', r':\1', path)
                key = f"{norm_method}:{norm_path}"
                
                has_hook = key in consumed_endpoints
                hook_name = hook_mapping.get(key)
                
                # Determine status
                if has_hook:
                    status = 'CONNECTED'
                else:
                    status = 'ORPHAN'
                
                endpoint = EndpointInfo(
                    layer=layer,
                    path=path,
                    method=method.upper(),
                    operation_id=operation_id,
                    tags=tags,
                    summary=summary,
                    has_hook=has_hook,
                    hook_name=hook_name,
                    has_component_surface=has_hook,  # Simplified assumption
                    component=None,
                    status=status
                )
                all_endpoints.append(endpoint)

# Summary by layer and status
summary = {}
for endpoint in all_endpoints:
    layer = endpoint.layer
    status = endpoint.status
    if layer not in summary:
        summary[layer] = {'CONNECTED': 0, 'ORPHAN': 0, 'SURFACE_GAP': 0, 'TYPE_GAP': 0, 'total': 0}
    summary[layer][status] += 1
    summary[layer]['total'] += 1

print(f"\nOpenAPI Endpoint Analysis Summary")
print(f"=" * 60)
total_connected = sum(s['CONNECTED'] for s in summary.values())
total_orphan = sum(s['ORPHAN'] for s in summary.values())
total = len(all_endpoints)

print(f"Total endpoints: {total}")
print(f"Connected: {total_connected} ({total_connected/total*100:.1f}%)")
print(f"Orphan: {total_orphan} ({total_orphan/total*100:.1f}%)")
print()

print("By Layer:")
print("-" * 60)
for layer, counts in sorted(summary.items()):
    orphan_pct = counts['ORPHAN'] / counts['total'] * 100 if counts['total'] > 0 else 0
    print(f"  {layer:25s}: {counts['total']:3d} total, {counts['CONNECTED']:3d} connected, {counts['ORPHAN']:3d} orphan ({orphan_pct:.1f}%)")

# Find interesting orphans (by tag/domain)
orphan_by_tag: Dict[str, int] = {}
for endpoint in all_endpoints:
    if endpoint.status == 'ORPHAN':
        for tag in endpoint.tags:
            orphan_by_tag[tag] = orphan_by_tag.get(tag, 0) + 1

print(f"\nOrphan Endpoints by Domain Tag:")
print("-" * 60)
for tag, count in sorted(orphan_by_tag.items(), key=lambda x: -x[1])[:15]:
    print(f"  {tag:30s}: {count}")

# Write output
output_path = Path("audit-output/track-b-openapi-analysis.json")
output_data = {
    "summary": {
        "total_endpoints": total,
        "connected": total_connected,
        "orphan": total_orphan,
        "by_layer": summary
    },
    "orphan_by_tag": orphan_by_tag,
    "endpoints": [asdict(e) for e in all_endpoints]
}
output_path.write_text(json.dumps(output_data, indent=2), encoding='utf-8')
print(f"\nOpenAPI analysis saved to: {output_path}")

# Print sample orphans
print("\nSample Orphan Endpoints (first 10):")
orphans = [e for e in all_endpoints if e.status == 'ORPHAN'][:10]
for o in orphans:
    tags_str = ", ".join(o.tags[:2]) if o.tags else "no tags"
    print(f"  {o.method:6s} {o.path:40s} | {o.layer:20s} | {tags_str}")
