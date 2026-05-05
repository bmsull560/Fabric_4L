import os
import subprocess
import sys

os.chdir(r"C:\Users\BBB\Fabric_4L")
cmd = [sys.executable, "-m", "pytest", "--co", "-n0", "--tb=long", "--timeout=10",
       "--import-mode=importlib", "--override-ini=addopts="]
r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

lines = r.stdout.split('\n')
for i, line in enumerate(lines):
    if 'ERROR collecting' in line:
        print("\n" + "="*60)
        print(lines[i])
        # Print traceback lines until blank line or next error
        for j in range(i+1, min(i+12, len(lines))):
            if lines[j].strip() == '' or 'ERROR collecting' in lines[j]:
                break
            if 'ModuleNotFoundError' in lines[j] or 'ImportError' in lines[j]:
                print(lines[j])
        print("="*60)
