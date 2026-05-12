#!/usr/bin/env python3
"""Run a bash command and capture output."""
import subprocess
import sys

cmd = sys.argv[1] if len(sys.argv) > 1 else "echo 'no command'"
result = subprocess.run(
    ["C:/tools/Git/bin/bash.exe", "-c", cmd],
    capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=300
)
print("EXIT_CODE:", result.returncode)
print("STDOUT:")
print(result.stdout)
print("STDERR:")
print(result.stderr)
