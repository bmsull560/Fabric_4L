import os
import subprocess
import sys

os.chdir(r"C:\Users\BBB\Fabric_4L\services\layer3-knowledge")
cmd = [sys.executable, "-m", "pytest", "-n0", "-q", "--tb=short", "--timeout=30",
       "tests/test_exception_handlers.py",
       "tests/test_tenant_context_extraction.py",
       "tests/test_tenant_isolation.py",
       "--override-ini=addopts="]
r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
print("STDOUT:")
print(r.stdout[-2000:] if len(r.stdout) > 2000 else r.stdout)
print("\nSTDERR:")
print(r.stderr[-500:] if r.stderr else "(empty)")
print("\nEXIT:", r.returncode)
