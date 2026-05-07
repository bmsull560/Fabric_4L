#!/usr/bin/env python3
"""
Ensure Pytest Collection Guard
Fails explicitly if pytest collects fewer than the expected number of tests,
or if it returns exit code 5 (no tests collected).
This prevents silent CI passes when test paths break or fixtures crash.
"""

import argparse
import subprocess
import sys
import re

def main():
    parser = argparse.ArgumentParser(description="Ensure minimum pytest collection")
    parser.add_argument("--dir", required=True, help="Directory to run pytest collection against")
    parser.add_argument("--min-tests", type=int, required=True, help="Minimum number of tests expected")
    args = parser.parse_args()

    print(f"Running pytest collection check for directory: {args.dir}")
    print(f"Expected minimum tests: {args.min_tests}")

    # Use python -m pytest to avoid path issues with pytest binary on Windows/Linux
    cmd = [sys.executable, "-m", "pytest", "--collect-only", "-q", args.dir]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    except Exception as e:
        print(f"Failed to execute pytest: {e}", file=sys.stderr)
        sys.exit(1)

    if result.returncode == 5:
        print(f"ERROR: Pytest exited with code 5 (No tests collected) in {args.dir}", file=sys.stderr)
        print(f"Pytest output:\n{result.stdout}\n{result.stderr}", file=sys.stderr)
        sys.exit(1)
        
    if result.returncode != 0 and result.returncode != 5:
        # Exit code 1 means tests collected but some might be failing to collect (import errors, etc.)
        # If it's a collection error, fail explicitly.
        if "error" in result.stdout.lower() or "error" in result.stderr.lower():
            print(f"ERROR: Pytest collection failed with errors in {args.dir} (exit code {result.returncode})", file=sys.stderr)
            print(f"Pytest output:\n{result.stdout}\n{result.stderr}", file=sys.stderr)
            sys.exit(1)

    # Parse the output to find "X tests collected"
    match = re.search(r'(\d+)\s+tests?\s+collected', result.stdout)
    if not match:
        match = re.search(r'collected\s+(\d+)\s+items?', result.stdout)
        
    if not match:
        print(f"ERROR: Could not parse test count from pytest output.", file=sys.stderr)
        print(f"Pytest output:\n{result.stdout}\n{result.stderr}", file=sys.stderr)
        sys.exit(1)

    collected = int(match.group(1))
    print(f"Collected {collected} tests.")

    if collected < args.min_tests:
        print(f"ERROR: Collected {collected} tests, which is less than the minimum required ({args.min_tests}).", file=sys.stderr)
        sys.exit(1)

    print("Collection check passed.")
    sys.exit(0)

if __name__ == "__main__":
    main()
