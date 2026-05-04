#!/usr/bin/env python3
"""
Generate Track B: Orphan Endpoint Registry Report
"""

import json
from pathlib import Path
from collections import defaultdict

# Load data
openapi_data = json.loads(Path("audit-output/track-b-openapi-analysis.json").read_text())

endpoints = openapi_data['endpoints']
orphan_by_tag = openapi_data['orphan_by_tag']

# Generate markdown report
md_lines = [
    "# Track B: API Archaeology — Orphan Endpoint Registry",
    "",
    "## Executive Summary",
    "",
    f"**Total Backend Endpoints:** {openapi_data['summary']['total_endpoints']}",
    f"**Connected (have frontend hooks):** {openapi_data['summary']['connected']}",
    f"**Orphan (no frontend surface):** {openapi_data['summary']['orphan']}",
    f"**Orphan Rate:** {openapi_data['summary']['orphan']/openapi_data['summary']['total_endpoints']*100:.1f}%",
    "",
    "## Orphan Rate by Layer",
    "",
    "| Layer | Total | Connected | Orphan | Orphan Rate |",
    "|-------|-------|-----------|--------|-------------|"
]

for layer, counts in sorted(openapi_data['summary']['by_layer'].items()):
    rate = counts['ORPHAN'] / counts['total'] * 100 if counts['total'] > 0 else 0
    md_lines.append(f"| {layer:20s} | {counts['total']:5d} | {counts['CONNECTED']:9d} | {counts['ORPHAN']:6d} | {rate:10.1f}% |")

md_lines.extend([
    "",
    "## Top Orphaned Domain Entities (by Tag)",
    "",
    "| Domain/Tag | Orphan Endpoints | Potential Frontend Surface |",
    "|------------|------------------|---------------------------|"
])

# Sort by count and add suggested pages
suggested_pages = {
    'Accounts': 'Accounts.tsx, CRM integration pages',
    'ValuePacks': 'ValuePacks.tsx',
    'state-inspector': 'HealthMonitor.tsx',
    'health': 'HealthMonitor.tsx',
    'ontology': 'OntologyEditor.tsx, EntityBrowser.tsx',
    'checkpoints': 'AgentWorkflows.tsx',
    'workflows': 'AgentWorkflows.tsx',
    'Integrations': 'Integrations.tsx',
    'Formulas': 'FormulaBuilder.tsx, FormulaList.tsx',
    'Models': 'MyModels.tsx',
    'Model Registry': 'MyModels.tsx',
    'ground-truth': 'DecisionTrace.tsx, Governance pages',
    'Graph': 'GraphExplorer.tsx',
    'Value Trees': 'ValueTreeExplorer.tsx',
    'Documents': 'EntityBrowser.tsx',
    'extraction': 'ExtractionEngine.tsx',
    'system': 'PlatformSettings.tsx',
    'Provenance': 'DecisionTrace.tsx',
    'Audit': 'DecisionTrace.tsx, governance pages',
    'Tenants': 'PlatformSettings.tsx (admin)',
    'Users': 'PermissionsAdmin.tsx',
    'API Keys': 'PermissionsAdmin.tsx',
    'Feature Flags': 'PlatformSettings.tsx',
}

for tag, count in sorted(orphan_by_tag.items(), key=lambda x: -x[1])[:25]:
    suggestion = suggested_pages.get(tag, 'Unknown')
    md_lines.append(f"| {tag:20s} | {count:16d} | {suggestion} |")

md_lines.extend([
    "",
    "## Critical Orphan Endpoints (High-Value, No Surface)",
    "",
    "These endpoints should power existing pages but have no frontend implementation:",
    ""
])

# Find critical orphans
orphans = [e for e in endpoints if e['status'] == 'ORPHAN']

# Group by domain area
critical_domains = {
    'Formulas': [],
    'Value Trees': [],
    'Graph': [],
    'ontology': [],
    'Accounts': [],
    'workflows': [],
    'ValuePacks': [],
}

for e in orphans:
    for tag in e.get('tags', []):
        if tag in critical_domains:
            critical_domains[tag].append(e)

for domain, eps in sorted(critical_domains.items(), key=lambda x: -len(x[1])):
    if not eps:
        continue
    md_lines.extend([
        f"### {domain}",
        "",
        "| Method | Path | Summary |",
        "|--------|------|---------|"
    ])
    for e in sorted(eps, key=lambda x: x['path'])[:10]:
        path = e['path'][:50] + '...' if len(e['path']) > 50 else e['path']
        md_lines.append(f"| {e['method']:6s} | `{path:50s}` | {e.get('summary', 'N/A')[:40]} |")
    if len(eps) > 10:
        md_lines.append(f"| ... | *{len(eps) - 10} more endpoints* | |")
    md_lines.append("")

md_lines.extend([
    "",
    "## Recommendations",
    "",
    "### Priority 1: Core Functionality",
    "1. **Accounts/CRM Integration** - 16 orphan endpoints for account management",
    "2. **Workflow Checkpoints** - 8 orphan endpoints for agent checkpoint/resume",
    "3. **Health Monitoring** - 12 orphan endpoints for system health",
    "",
    "### Priority 2: Knowledge Layer",
    "1. **Ontology Management** - 14 orphan endpoints for ontology CRUD",
    "2. **Graph Context** - Entity context endpoints for GraphExplorer",
    "3. **Value Trees** - Path traversal endpoints for ValueTreeExplorer",
    "",
    "### Priority 3: Platform",
    "1. **Tenant Management** - 5 orphan endpoints for multi-tenant admin",
    "2. **User/Permission** - 5+ orphan endpoints for access control",
    "3. **Ground Truth** - 13 orphan endpoints for evaluation/evidence",
])

# Write report
md_path = Path("audit-output/track-b-orphan-registry.md")
md_path.write_text('\n'.join(md_lines), encoding='utf-8')
print(f"Track B report saved to: {md_path}")

# Print summary
print(f"\n{'='*60}")
print(f"TRACK B: ORPHAN ENDPOINT REGISTRY - SUMMARY")
print(f"{'='*60}")
print(f"Total Endpoints: {openapi_data['summary']['total_endpoints']}")
print(f"Connected: {openapi_data['summary']['connected']}")
print(f"Orphan: {openapi_data['summary']['orphan']}")
print(f"Orphan Rate: {openapi_data['summary']['orphan']/openapi_data['summary']['total_endpoints']*100:.1f}%")
print(f"")
print(f"Top 5 Orphaned Domains:")
for tag, count in sorted(orphan_by_tag.items(), key=lambda x: -x[1])[:5]:
    print(f"  {tag:25s}: {count} endpoints")
