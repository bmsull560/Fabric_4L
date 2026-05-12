#!/usr/bin/env python3
"""Run a command and save output to a file."""
import subprocess
import sys

cmd = sys.argv[1]
outfile = sys.argv[2]
result = subprocess.run(
    ["C:/tools/Git/bin/bash.exe", "-c", cmd],
    capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300
)
with open(outfile, "w", encoding="utf-8") as f:
    f.write("EXIT_CODE: " + str(result.returncode) + "\n")
    f.write("STDOUT:\n" + result.stdout + "\n")
    f.write("STDERR:\n" + result.stderr + "\n")
print("saved to", outfile, "exit_code=", result.returncode)
