#!/usr/bin/env python3
"""
Generate Route Integrity Matrix for Tri-Track Audit (Track A)
Combines route extraction, hook analysis, and data source classification.
"""

import csv
import json
import sys
from pathlib import Path
from typing import Dict, List, Any

# Constants for output formatting
MAX_HOOK_LEN = 25
MAX_HOOK_TRUNCATED = 22
MAX_ENDPOINT_LEN = 35
MAX_ENDPOINT_TRUNCATED = 32
MAX_PATH_LEN = 40
MAX_PATH_TRUNCATED = 37

def load_json_file(path: Path) -> Dict[str, Any]:
    """Load and validate JSON file."""
    if not path.exists():
        print(f"ERROR: Required file not found: {path}", file=sys.stderr)
        print(f"Run the route extraction and hook analysis scripts first.", file=sys.stderr)
        sys.exit(1)
    
    try:
        content = path.read_text(encoding='utf-8')
        data = json.loads(content)
        return data
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in {path}: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Failed to read {path}: {e}", file=sys.stderr)
        sys.exit(1)


def truncate_string(value: str, max_len: int, truncated_len: int) -> str:
    """Truncate string with ellipsis if too long."""
    if not value:
        return value
    if len(value) <= max_len:
        return value
    return value[:truncated_len] + '...'


# Load data
routes_path = Path("audit-output/track-a-route-extraction.json")
hook_path = Path("audit-output/track-a-hook-analysis.json")

routes_data = load_json_file(routes_path)
hook_data = load_json_file(hook_path)

# Build component -> hooks mapping (simplified based on naming conventions)
component_hook_map = {
    'Accounts': ['useAccounts', 'useCreateAccount'],
    'FormulaList': ['useFormulas'],
    'FormulaBuilder': ['useFormula', 'useSubmitFormula', 'useFormulaApprovals'],
    'EntityBrowser': ['useEntities'],
    'GraphExplorer': ['useGraphQuery', 'useSubgraph'],
    'ValuePacks': ['useValuePacks', 'useApplyValuePack'],
    'BillingSettings': ['useBilling'],
    'UsageDashboard': ['useUsage'],
    'IngestionJobs': ['useIngestion'],
    'ExtractionEngine': ['useExtraction', 'useRunExtraction'],
    'AgentWorkflows': ['useWorkflows'],
    'BusinessCase': ['useBusinessCases'],
    'BusinessCaseList': ['useBusinessCases'],
    'DecisionTrace': ['useProvenance'],
    'BenchmarkPolicies': ['useBenchmarks', 'useBenchmarkPolicies', 'useUpdateBenchmarkPolicy'],
    'VariableRegistry': ['useVariables'],
    'PlatformSettings': ['usePlatformSettings'],
    'HealthMonitor': ['useSystemHealth', 'useHealthAlerts'],
    'ValueTreeExplorer': ['useValueTrees'],
    'MyModels': ['useModels'],
    'OntologyEditor': ['useOntology'],
    'Integrations': ['useIntegrations'],
    'SourceConfiguration': ['useSources'],
    'SignalsTab': ['useOpportunities'],  # May be mock
    'DriversTab': [],  # Unknown
    'EvidenceTab': [],  # Unknown
    'StakeholdersTab': [],  # Unknown
    'ActionPlanTab': [],  # Unknown
    'ValueModelTab': [],  # Unknown
    'NarrativeTab': [],  # Unknown
}

# Build hook -> color mapping
hook_colors = {h['name']: h['data_source_color'] for h in hook_data['hooks']}
hook_endpoints = {h['name']: h.get('api_endpoints', []) for h in hook_data['hooks']}

# Classify routes
classified_routes = []

for route in routes_data['routes']:
    component = route['component']
    
    # Skip redirects
    if route['category'] == 'redirect':
        classified_routes.append({
            **route,
            'hook_name': 'N/A (redirect)',
            'backend_endpoint': route.get('redirect_target', ''),
            'data_source_color': 'redirect',
            'notes': f"Redirects to {route.get('redirect_target', 'unknown')}"
        })
        continue
    
    # Get hooks for this component
    hooks = component_hook_map.get(component, [])
    
    if not hooks:
        # Unknown component - likely incomplete implementation
        classified_routes.append({
            **route,
            'hook_name': 'UNKNOWN',
            'backend_endpoint': '',
            'data_source_color': 'red',
            'notes': 'No hooks mapped - likely hardcoded or incomplete'
        })
        continue
    
    # Check hook colors
    colors = [hook_colors.get(h, 'unknown') for h in hooks]
    endpoints = []
    for h in hooks:
        endpoints.extend(hook_endpoints.get(h, []))
    
    # Determine overall color
    if 'red' in colors:
        color = 'red'
    elif 'green' in colors:
        color = 'green'
    elif 'yellow' in colors:
        color = 'yellow'
    else:
        color = 'unknown'
    
    primary_hook = hooks[0] if hooks else 'NONE'
    primary_endpoint = endpoints[0] if endpoints else 'N/A'
    
    # Generate notes
    notes = []
    if color == 'green':
        notes.append(f"Live integration via {primary_hook}")
    elif color == 'yellow':
        notes.append(f"Generic endpoint passthrough via {primary_hook}")
    elif color == 'red':
        notes.append(f"Hardcoded/mock data in {primary_hook}")
    else:
        notes.append("No backend integration found")
    
    if route.get('required_tier') == 'admin':
        notes.append("Admin tier route")
    elif route.get('required_tier') == 'advanced':
        notes.append("Advanced tier route")
    
    classified_routes.append({
        **route,
        'hook_name': primary_hook,
        'backend_endpoint': primary_endpoint,
        'data_source_color': color,
        'notes': '; '.join(notes)
    })

# Count by color
color_counts = {}
for r in classified_routes:
    c = r['data_source_color']
    color_counts[c] = color_counts.get(c, 0) + 1

# Write CSV
csv_path = Path("audit-output/track-a-route-matrix.csv")
with open(csv_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=[
        'path', 'component', 'tier', 'category', 'required_tier',
        'hook_name', 'backend_endpoint', 'data_source_color', 'notes'
    ])
    writer.writeheader()
    for r in classified_routes:
        writer.writerow({
            'path': r['path'],
            'component': r['component'],
            'tier': r['tier'],
            'category': r['category'],
            'required_tier': r.get('required_tier', ''),
            'hook_name': r['hook_name'],
            'backend_endpoint': r['backend_endpoint'],
            'data_source_color': r['data_source_color'],
            'notes': r['notes']
        })

print(f"Route matrix CSV saved to: {csv_path}")

# Write Markdown summary
md_path = Path("audit-output/track-a-route-matrix.md")
md_lines = [
    "# Track A: Route Integrity Matrix",
    "",
    "## Executive Summary",
    "",
    f"**Total Routes Analyzed:** {len(classified_routes)}",
    "",
    "### Data Source Distribution",
    "",
    "| Color | Status | Count | Percentage |",
    "|-------|--------|-------|------------|"
]

total = len(classified_routes)
for color in ['green', 'yellow', 'red', 'redirect', 'unknown']:
    count = color_counts.get(color, 0)
    pct = count / total * 100 if total > 0 else 0
    status_map = {
        'green': 'Live backend integration',
        'yellow': 'Generic endpoint passthrough',
        'red': 'Hardcoded mock/orphaned',
        'redirect': 'Legacy redirects',
        'unknown': 'Unknown/unevaluated'
    }
    md_lines.append(f"| **{color.upper()}** | {status_map.get(color, color)} | {count} | {pct:.1f}% |")

# Calculate facade percentage (red + unknown authenticated routes)
auth_routes = [r for r in classified_routes if r['category'] == 'authenticated']
facade_count = sum(1 for r in auth_routes if r['data_source_color'] in ['red', 'unknown'])
facade_pct = facade_count / len(auth_routes) * 100 if auth_routes else 0

md_lines.extend([
    "",
    f"### Facade Problem: {facade_pct:.1f}%",
    "",
    f"**{facade_count}** of **{len(auth_routes)}** authenticated routes are non-functional facades (render hardcoded data, mocks, or have no backend integration).",
    "",
    "## Route Detail by Category",
    ""
])

# Group by color and list routes
for color in ['green', 'yellow', 'red', 'unknown']:
    routes = [r for r in classified_routes if r['data_source_color'] == color]
    if not routes:
        continue
    
    status_title = {
        'green': 'GREEN: Live Backend Integration',
        'yellow': 'YELLOW: Generic Endpoint Passthrough',
        'red': 'RED: Hardcoded/Mock/Orphaned',
        'unknown': 'UNKNOWN: Unevaluated/Incomplete'
    }.get(color, color.upper())
    
    md_lines.extend([
        f"### {status_title}",
        "",
        "| Route | Component | Hook | Backend Endpoint |",
        "|-------|-----------|------|------------------|"
    ])
    
    for r in routes[:30]:  # Limit to first 30 for brevity
        hook = truncate_string(r['hook_name'], MAX_HOOK_LEN, MAX_HOOK_TRUNCATED)
        endpoint = truncate_string(
            r['backend_endpoint'] if r['backend_endpoint'] else 'N/A',
            MAX_ENDPOINT_LEN, MAX_ENDPOINT_TRUNCATED
        )
        path_display = truncate_string(r['path'], MAX_PATH_LEN, MAX_PATH_TRUNCATED)
        md_lines.append(f"| `{path_display}` | {r['component']} | {hook} | {endpoint} |")
    
    if len(routes) > 30:
        md_lines.append(f"| ... | *{len(routes) - 30} more routes* | | |")
    
    md_lines.append("")

md_path.write_text('\n'.join(md_lines), encoding='utf-8')
print(f"Route matrix Markdown saved to: {md_path}")

# Print summary
print(f"\n{'='*60}")
print(f"TRACK A: ROUTE INTEGRITY MATRIX - SUMMARY")
print(f"{'='*60}")
print(f"Total Routes: {len(classified_routes)}")
print(f"")
print(f"Data Source Distribution:")
for color in ['green', 'yellow', 'red', 'redirect', 'unknown']:
    count = color_counts.get(color, 0)
    pct = count / total * 100 if total > 0 else 0
    print(f"  {color.upper():10s}: {count:3d} ({pct:5.1f}%)")
print(f"")
print(f"FACADE PROBLEM: {facade_pct:.1f}% of authenticated routes")
print(f"  - {facade_count} non-functional authenticated routes")
print(f"  - {len(auth_routes) - facade_count} functional authenticated routes")
