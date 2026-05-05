import os
import subprocess
import sys

os.chdir(r"C:\Users\BBB\Fabric_4L")
cmd = [sys.executable, "-m", "pytest", "--co", "-n0", "--tb=long", "--timeout=10",
       "--override-ini=addopts="]
r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

lines = r.stdout.split('\n')
for i, line in enumerate(lines):
    if 'ERROR collecting' in line or 'ImportError while loading conftest' in line or 'ModuleNotFoundError' in line:
        # Print this line and next few lines for context
        for j in range(i, min(i+8, len(lines))):
            print(lines[j])
        print("---")
