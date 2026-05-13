from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
LAYER6_SRC = REPO_ROOT / "services" / "layer6-benchmarks" / "src"


def test_layer6_service_src_directory_exists() -> None:
    assert LAYER6_SRC.is_dir(), f"Missing required Layer 6 service source directory: {LAYER6_SRC}"


def test_layer6_service_entrypoint_exists() -> None:
    entrypoint = LAYER6_SRC / "api" / "main.py"
    assert entrypoint.is_file(), f"Missing Layer 6 API entrypoint required by Docker CMD: {entrypoint}"
