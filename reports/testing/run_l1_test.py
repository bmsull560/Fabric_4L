import os
import subprocess
import sys

os.chdir(r"C:\Users\BBB\Fabric_4L")
cmd = [sys.executable, "-m", "pytest", "-n0", "-q", "--tb=short", "--timeout=30",
       "services/layer1-ingestion/tests/unit/test_pdf_adapter.py",
       "services/layer1-ingestion/tests/unit/test_pii_scanner.py",
       "services/layer1-ingestion/tests/unit/test_playwright_crawler.py",
       "--override-ini=addopts="]
r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
print("STDOUT:")
print(r.stdout[-2000:] if len(r.stdout) > 2000 else r.stdout)
print("\nSTDERR:")
print(r.stderr[-500:] if r.stderr else "(empty)")
print("\nEXIT:", r.returncode)
