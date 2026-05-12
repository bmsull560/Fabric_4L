import os

SKIP_DIRS = {".venv", ".tmp", ".mypy_cache", ".pytest_cache", ".ruff_cache", "__pycache__", ".hypothesis"}


def lacks_future_annotations(root_dir: str) -> None:
    for r, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            if f.endswith(".py"):
                path = os.path.join(r, f)
                try:
                    with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                        content = fh.read(500)
                    if "from __future__ import annotations" not in content:
                        print(path)
                except OSError:
                    pass


if __name__ == "__main__":
    lacks_future_annotations(r"c:\Users\BBB\Fabric_4L\services\layer4-agents\src")
