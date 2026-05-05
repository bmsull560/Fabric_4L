import os
import subprocess
import sys

os.chdir(r"C:\Users\BBB\Fabric_4L")
cmd = [sys.executable, "-m", "pytest", "--co", "-n0", "-q", "--tb=short", "--timeout=10",
       "--import-mode=importlib", "--override-ini=addopts="]
r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
print("STDOUT:")
print(r.stdout[-3000:] if len(r.stdout) > 3000 else r.stdout)
print("\nSTDERR:")
print(r.stderr[-3000:] if r.stderr else "(empty)")
print("\nEXIT:", r.returncode)
