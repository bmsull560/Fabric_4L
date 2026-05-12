import subprocess, sys
result = subprocess.run(
    [sys.executable, "-m", "pytest", "services/layer1-ingestion/tests/", "--collect-only", "--tb=long"],
    capture_output=True, text=True, cwd=r"C:\Users\BBB\Fabric_4L"
)
with open("layer1_collect_errors.txt", "w") as f:
    f.write("STDOUT:\n")
    f.write(result.stdout)
    f.write("\nSTDERR:\n")
    f.write(result.stderr)
    f.write(f"\nReturn code: {result.returncode}\n")
print("done")
