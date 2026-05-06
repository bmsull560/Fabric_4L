"""Prevent accidental runtime placeholders from shipping."""

from pathlib import Path


def test_no_runtime_notimplementederror_outside_allowlist() -> None:
    root = Path(__file__).resolve().parents[2]
    runtime_roots = (
        root / "packages" / "shared" / "src",
        root / "services" / "layer2-extraction" / "src",
        root / "services" / "layer3-knowledge" / "src",
        root / "value_fabric",
    )
    allowlist = {
        "packages/shared/src/value_fabric/shared/rate_limiting/middleware.py": "Intentional fallback branch for optional integration boundary.",
    }

    violations: list[str] = []
    for runtime_root in runtime_roots:
        for path in runtime_root.rglob("*.py"):
            rel = str(path.relative_to(root))
            if "/tests/" in rel or rel in allowlist:
                continue
            for idx, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
                normalized = line.strip()
                if "raise NotImplementedError" in normalized:
                    violations.append(f"{rel}:{idx}")

    assert not violations, (
        "Found disallowed NotImplementedError in runtime code. "
        "Either implement it or add explicit allowlist justification.\n"
        + "\n".join(violations)
    )
