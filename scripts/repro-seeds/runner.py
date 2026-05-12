#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path


def _stable_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def apply_seed_pack(pack_dir: Path, migration_revision: str, output_dir: Path) -> Path:
    manifest = json.loads((pack_dir / "manifest.json").read_text())
    if migration_revision != manifest["required_migration_revision"]:
        raise ValueError(
            f"Migration revision mismatch: expected {manifest['required_migration_revision']} got {migration_revision}"
        )

    payload = json.loads((pack_dir / "payload.json").read_text())
    rng = random.Random(manifest["deterministic_rng_seed"])
    payload["_repro"] = {
        "seed_id": manifest["seed_id"],
        "migration_revision": migration_revision,
        "nonce": rng.randint(0, 10**9),
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    out_file = output_dir / f"{manifest['seed_id']}.applied.json"
    out_file.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return out_file


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply reproducibility seed pack")
    parser.add_argument("--pack-dir", required=True)
    parser.add_argument("--migration-revision", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    out_file = apply_seed_pack(Path(args.pack_dir), args.migration_revision, Path(args.output_dir))
    print(json.dumps({"output": str(out_file), "sha256": _stable_sha256(out_file)}))


if __name__ == "__main__":
    main()
