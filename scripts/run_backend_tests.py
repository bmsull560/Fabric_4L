#!/usr/bin/env python3
"""Run backend tests for a service and save output."""
import subprocess
import sys

service = sys.argv[1]
outfile = sys.argv[2]
result = subprocess.run(
    ["C:/tools/Git/bin/bash.exe", "-c", f"cd /c/Users/BBB/Fabric_4L/services/{service} && python -m pytest tests/ -v --tb=short 2>&1 | head -150"],
    capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300
)
with open(outfile, "w", encoding="utf-8") as f:
    f.write("EXIT_CODE: " + str(result.returncode) + "\n")
    f.write("STDOUT:\n" + result.stdout + "\n")
    f.write("STDERR:\n" + result.stderr + "\n")
print("saved to", outfile, "exit_code=", result.returncode)
