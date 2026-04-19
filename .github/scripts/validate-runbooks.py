#!/usr/bin/env python3
"""
Runbook Validation Script

Validates that all alerts in monitoring/alerting/rules.yml have corresponding
runbook files in docs/runbooks/. Exit code 0 if valid, 1 if any issues found.

Usage:
    python .github/scripts/validate-runbooks.py
    python .github/scripts/validate-runbooks.py --verbose
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple
import argparse


def extract_runbook_urls(rules_file: Path) -> List[Tuple[str, str]]:
    """Extract all runbook URLs from the rules.yml file.
    
    Returns list of (alert_name, runbook_url) tuples.
    """
    content = rules_file.read_text(encoding='utf-8')
    
    # Split into alert blocks and extract runbook_url from each
    # Alert blocks start with "- alert:" and end at the next "- alert:" or end of rules section
    alert_blocks = re.split(r'\n      - alert:', content)
    
    results = []
    for block in alert_blocks[1:]:  # Skip content before first alert
        # Extract alert name from first line
        name_match = re.match(r'\s*(\w+)', block)
        if not name_match:
            continue
        alert_name = name_match.group(1)
        
        # Extract runbook_url from this block only
        url_match = re.search(r'runbook_url:\s*"([^"]+)"', block)
        if url_match:
            results.append((alert_name, url_match.group(1)))
    
    return results


def extract_runbook_path(url: str) -> Path | None:
    """Extract the local file path from a runbook URL.
    
    Converts GitHub URLs like:
        https://github.com/bmsull560/Fabric_4L/blob/main/docs/runbooks/xxx.md
    To local paths like:
        docs/runbooks/xxx.md
    """
    # Match GitHub blob URLs
    github_pattern = re.compile(
        r'https://github\.com/[^/]+/[^/]+/blob/[^/]+/(.+)'
    )
    match = github_pattern.match(url)
    
    if match:
        path_str = match.group(1)
        return Path(path_str)
    
    return None


def validate_runbooks(
    repo_root: Path,
    verbose: bool = False
) -> Tuple[bool, List[str]]:
    """Validate all runbook URLs point to existing files.
    
    Returns (is_valid, error_messages).
    """
    rules_file = repo_root / "monitoring" / "alerting" / "rules.yml"
    
    if not rules_file.exists():
        return False, [f"Rules file not found: {rules_file}"]
    
    runbook_refs = extract_runbook_urls(rules_file)
    errors = []
    warnings = []
    
    if verbose:
        print(f"Found {len(runbook_refs)} alerts with runbook_url annotations\n")
    
    for alert_name, url in runbook_refs:
        runbook_path = extract_runbook_path(url)
        
        if runbook_path is None:
            errors.append(
                f"[{alert_name}] Invalid runbook URL format (not a GitHub blob URL): {url}"
            )
            continue
        
        full_path = repo_root / runbook_path
        
        if not full_path.exists():
            errors.append(
                f"[{alert_name}] Runbook file not found: {runbook_path}"
            )
        else:
            if verbose:
                print(f"  [OK] {alert_name} -> {runbook_path}")
            
            # Validate runbook has required sections
            content = full_path.read_text(encoding='utf-8')
            required_sections = ['## Symptoms', '## Diagnosis', '## Remediation', '## Escalation']
            missing_sections = []
            
            for section in required_sections:
                if section not in content:
                    missing_sections.append(section)
            
            if missing_sections:
                warnings.append(
                    f"[{alert_name}] Runbook missing sections: {', '.join(missing_sections)}"
                )
    
    return len(errors) == 0, errors + warnings


def main():
    parser = argparse.ArgumentParser(
        description="Validate runbook files match alert annotations"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Print detailed validation output"
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Repository root directory (default: auto-detect)"
    )
    
    args = parser.parse_args()
    
    # Determine repo root
    if args.root:
        repo_root = args.root
    else:
        # Auto-detect: script is at .github/scripts/, so go up 2 levels
        script_dir = Path(__file__).parent.resolve()
        repo_root = script_dir.parent.parent
    
    is_valid, messages = validate_runbooks(repo_root, verbose=args.verbose)
    
    # Print results
    if messages:
        print("\nValidation issues:")
        for msg in messages:
            print(f"  - {msg}")
    
    if is_valid:
        print("\nRunbook validation: PASSED")
        sys.exit(0)
    else:
        print("\nRunbook validation: FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()
