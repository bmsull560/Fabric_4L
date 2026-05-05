import os
import subprocess
import sys

os.chdir(r"C:\Users\BBB\Fabric_4L")
tests = [
    "services/layer1-ingestion/tests/unit/test_crawler_telemetry.py",
    "services/layer2-extraction/tests/test_extract_and_ingest_pipeline.py",
    "services/layer2-extraction/tests/test_sse_streaming.py",
]
for t in tests:
    cmd = [sys.executable, "-m", "pytest", "--co", "-n0", "--tb=long", "--timeout=10",
           "--override-ini=addopts=", t]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    # Find the last error line
    for line in r.stdout.split('\n')[-20:]:
        if line.strip() and ('ERROR' in line or 'ModuleNotFoundError' in line or 'ImportError' in line or 'E ' in line):
            print(f"{t}: {line.strip()}")
