import os
import subprocess
import sys

os.chdir(r"C:\Users\BBB\Fabric_4L")
tests = [
    "services/layer1-ingestion/tests/unit/test_crawler_telemetry.py",
    "services/layer2-extraction/tests/test_extract_and_ingest_pipeline.py",
    "services/layer2-extraction/tests/test_sse_streaming.py",
]

with open(r"C:\Users\BBB\AppData\Local\Temp\diag_out.txt", "w") as f:
    for t in tests:
        cmd = [sys.executable, "-m", "pytest", "--co", "-n0", "--tb=long", "--timeout=10",
               "--override-ini=addopts=", t]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        f.write(f"\n{'='*60}\n{t}\n{'='*60}\n")
        f.write(r.stdout[-1000:] if len(r.stdout) > 1000 else r.stdout)
        f.write("\n")
