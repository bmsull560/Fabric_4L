#!/usr/bin/env python3
"""
Hook Analysis Script for Tri-Track Audit (Track A)
Analyzes all hooks to map them to backend endpoints and classify data source color.
"""

import re
import json
import sys
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any

# Regex patterns for analysis (compiled once for performance)
API_PATTERN = re.compile(r'apiClient\.(get|post|put|patch|delete)\(["\']([^"\']+)')
QUERY_PATTERN = re.compile(r'useQuery\(\s*\{[^}]*queryKey:\s*([^,\s]+)')
MUTATION_PATTERN = re.compile(r'useMutation\(\s*\{[^}]*mutationKey:\s*([^,\s]+)')
MOCK_PATTERN = re.compile(r'return\s*\{[^}]*mock|hardcoded|static', re.IGNORECASE)
TODO_PATTERN = re.compile(r'TODO|FIXME|XXX', re.IGNORECASE)
ENDPOINT_IN_URL = re.compile(r'/v\d+/[^"\']+')
EXPORT_PATTERN = re.compile(r'export\s+(?:const|function)\s+(\w+)')

@dataclass
class HookAnalysis:
    name: str
    file: str
    imports: List[str]
    api_endpoints: List[str]
    query_keys: List[str]
    mutation_keys: List[str]
    has_types: bool
    has_error_handling: bool
    is_mock: bool  # If hook returns hardcoded data
    data_source_color: str  # 'green', 'yellow', 'red', 'unknown'


def load_hook_files(hooks_dir: Path) -> List[Path]:
    """Find and validate hook files, excluding tests."""
    if not hooks_dir.exists():
        print(f"ERROR: Hooks directory not found: {hooks_dir}", file=sys.stderr)
        sys.exit(1)
    
    hook_files = list(hooks_dir.glob("use*.ts"))
    
    if not hook_files:
        print(f"WARNING: No hook files found in {hooks_dir}", file=sys.stderr)
        return []
    
    # Exclude test files
    hook_files = [f for f in hook_files if not f.name.endswith(".test.ts")]
    return hook_files


def analyze_hook_file(hook_file: Path) -> Optional[HookAnalysis]:
    """Analyze a single hook file for API endpoints, queries, and data patterns."""
    try:
        content = hook_file.read_text(encoding='utf-8')
    except Exception as e:
        print(f"WARNING: Failed to read {hook_file}: {e}", file=sys.stderr)
        return None

    # Extract hook name from exports
    export_match = EXPORT_PATTERN.search(content)
    hook_name = export_match.group(1) if export_match else hook_file.stem
    
    # Find API endpoints
    api_endpoints = []
    for match in API_PATTERN.finditer(content):
        method = match.group(1).upper()
        path = match.group(2)
        api_endpoints.append(f"{method} {path}")
    
    # Also find endpoints in URL strings
    for match in ENDPOINT_IN_URL.finditer(content):
        endpoint = match.group(0)
        if endpoint not in [e.split(' ', 1)[1] for e in api_endpoints]:
            # Check if preceded by a method
            before = content[max(0, match.start()-100):match.start()]
            method = None
            for m in ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']:
                if m in before.upper():
                    method = m
                    break
            if method:
                api_endpoints.append(f"{method} {endpoint}")
    
    # Find query keys
    query_keys = []
    for match in QUERY_PATTERN.finditer(content):
        query_keys.append(match.group(1))
    
    # Find mutation keys
    mutation_keys = []
    for match in MUTATION_PATTERN.finditer(content):
        mutation_keys.append(match.group(1))
    
    # Check for mock/hardcoded data
    is_mock = bool(MOCK_PATTERN.search(content)) or bool(TODO_PATTERN.search(content))
    
    # Determine data source color
    if is_mock:
        color = 'red'
    elif not api_endpoints:
        # Check if it's a utility hook
        if 'useQuery' in content or 'useMutation' in content:
            color = 'yellow'  # Uses generic endpoint
        else:
            color = 'unknown'  # No API calls
    elif len(api_endpoints) >= 1:
        # Check if endpoints are specific or generic
        specific_endpoints = [e for e in api_endpoints if not e.endswith('/') and len(e.split('/')[-1]) > 1]
        if specific_endpoints:
            color = 'green'
        else:
            color = 'yellow'
    else:
        color = 'unknown'
    
    # Check for error handling
    has_error_handling = 'error' in content.lower() and ('onError' in content or 'catch' in content or 'throw' in content)
    
    # Check for proper types (not using any)
    has_types = 'any' not in content.lower() or ': any' not in content
    
    return HookAnalysis(
        name=hook_name,
        file=hook_file.name,
        imports=[],  # Would need full AST parsing
        api_endpoints=list(set(api_endpoints)),
        query_keys=query_keys,
        mutation_keys=mutation_keys,
        has_types=has_types,
        has_error_handling=has_error_handling,
        is_mock=is_mock,
        data_source_color=color
    )


def main() -> None:
    """Main entry point for hook analysis."""
    # Read all hook files
    hooks_dir = Path("frontend/client/src/hooks")
    hook_files = load_hook_files(hooks_dir)
    
    if not hook_files:
        print("No hook files to analyze.", file=sys.stderr)
        sys.exit(0)
    
    print(f"Analyzing {len(hook_files)} hook files...")
    
    hook_analyses = []
    for hook_file in sorted(hook_files):
        analysis = analyze_hook_file(hook_file)
        if analysis:
            hook_analyses.append(analysis)
    
    # Summary
    print(f"\nHook Analysis Summary")
    print(f"=" * 60)
    color_counts: Dict[str, int] = {}
    for h in hook_analyses:
        color_counts[h.data_source_color] = color_counts.get(h.data_source_color, 0) + 1
    
    for color, count in sorted(color_counts.items()):
        print(f"  {color.upper()}: {count} hooks")
    
    # Ensure output directory exists
    output_dir = Path("audit-output")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Write output
    output_path = output_dir / "track-a-hook-analysis.json"
    output_data = {
        "summary": {
            "total_hooks": len(hook_analyses),
            "by_color": color_counts,
            "green_live": color_counts.get('green', 0),
            "yellow_generic": color_counts.get('yellow', 0),
            "red_mock": color_counts.get('red', 0),
            "unknown": color_counts.get('unknown', 0)
        },
        "hooks": [asdict(h) for h in hook_analyses]
    }
    output_path.write_text(json.dumps(output_data, indent=2), encoding='utf-8')
    print(f"\nHook analysis saved to: {output_path}")
    
    # Print sample
    print("\nFirst 10 hooks:")
    for h in hook_analyses[:10]:
        endpoints_str = f" ({len(h.api_endpoints)} endpoints)" if h.api_endpoints else ""
        print(f"  {h.name:30s} | {h.data_source_color:8s} | {h.file:30s}{endpoints_str}")


if __name__ == "__main__":
    main()
