import os
import re

PATTERN = re.compile(r"c:\\\\Users\\\\BBB|C:\\\\Users\\\\BBB|/Users/BBB", re.IGNORECASE)

def search(root_dir: str) -> None:
    skip_dirs = {".venv", ".tmp", ".mypy_cache", ".pytest_cache", ".ruff_cache", "__pycache__"}
    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for f in files:
            if f.endswith(".py"):
                path = os.path.join(root, f)
                try:
                    with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                        content = fh.read()
                        if PATTERN.search(content):
                            print(path)
                except OSError:
                    pass

if __name__ == "__main__":
    search(r"c:\Users\BBB\Fabric_4L\services\layer4-agents")
    search(r"c:\Users\BBB\Fabric_4L\value_fabric\layer4")
