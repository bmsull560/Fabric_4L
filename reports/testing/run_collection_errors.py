import os
import re
import subprocess
import sys

os.chdir(r"C:\Users\BBB\Fabric_4L")
cmd = [sys.executable, "-m", "pytest", "--co", "-n0", "--tb=short", "--timeout=10",
       "--override-ini=addopts="]
r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

# Find all unique error patterns
errors = re.findall(r'ERROR collecting (.+?)\n(.+?)(?=\nERROR collecting|\n={3,}|\Z)', r.stdout, re.DOTALL)
print(f"Total errors: {len(errors)}")
for i, (file_, msg) in enumerate(errors[:10], 1):
    # Extract the actual exception message (last line usually)
    lines = msg.strip().split('\n')
    last_line = lines[-1] if lines else ""
    print(f"\n{i}. {file_.strip()}")
    print(f"   {last_line.strip()}")
