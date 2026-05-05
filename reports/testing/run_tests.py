import subprocess
import sys

def run(tests, args=None):
    cmd = [sys.executable, "-m", "pytest"] + tests + (args or ["-n0", "-q", "--tb=short", "--timeout=30"])
    r = subprocess.run(cmd, cwd=r"C:\Users\BBB\Fabric_4L", capture_output=True, text=True, timeout=60)
    print(r.stdout[-2000:])
    if r.stderr:
        print("STDERR:", r.stderr[-500:])
    print("EXIT:", r.returncode)

if __name__ == "__main__":
    run([r"services\layer3-knowledge\tests\test_tenant_isolation.py"])
