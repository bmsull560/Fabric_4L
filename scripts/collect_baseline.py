import subprocess
import re
import sys

print("Running pytest --collect-only...")
result = subprocess.run(
    [sys.executable, "-m", "pytest", "--collect-only", "--strict-markers", "--tb=long"],
    capture_output=True,
    text=True,
    encoding="utf-8",
    errors="replace"
)

content = result.stdout + result.stderr

# Find all ERROR blocks with more context
errors = []
for m in re.finditer(r'ERROR\s+(.+?)(?=\nERROR|\n=+ |\Z)', content, re.DOTALL):
    block = m.group(0)
    lines = block.splitlines()
    path = lines[0].replace("ERROR ", "").strip()
    # Extract the last meaningful error line
    exc = "Unknown"
    for line in reversed(lines):
        if any(e in line for e in ["AttributeError", "ImportError", "ModuleNotFoundError", "Failed:", "ValueError", "TypeError", "SyntaxError", "KeyError", "NameError"]):
            exc = line.strip()
            break
    errors.append((path, exc))

print(f"\n{'='*70}")
print(f"BASELINE COLLECTION SUMMARY")
print(f"{'='*70}")
# Extract total collected from the summary line
summary_match = re.search(r'(\d+) tests collected', content)
if summary_match:
    print(f"Total tests collected: {summary_match.group(1)}")
print(f"Collection errors: {len(errors)}")
print(f"\nFirst 10 collection errors:")
for path, exc in errors[:10]:
    print(f"  {path}")
    print(f"    -> {exc[:150]}")
print(f"\n... ({len(errors) - 10} more errors omitted)" if len(errors) > 10 else "")

# Save full output for reference
with open("pytest_baseline_collect.txt", "w", encoding="utf-8") as f:
    f.write(content)
print(f"\nFull output saved to: pytest_baseline_collect.txt")
