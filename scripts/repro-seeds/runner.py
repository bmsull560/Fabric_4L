#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import random
import subprocess
from pathlib import Path


def _stable_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _run_migration(migrate_cmd: str | None, revision: str) -> None:
    if not migrate_cmd:
        return
    cmd = [token.format(revision=revision) for token in migrate_cmd.split()]
    subprocess.run(cmd, check=True)


def apply_seed_pack(pack_dir: Path, migration_revision: str, output_dir: Path, migrate_cmd: str | None = None) -> Path:
    manifest = json.loads((pack_dir / "manifest.json").read_text())
    expected_revision = manifest["required_migration_revision"]
    if migration_revision != expected_revision:
        raise ValueError(
            f"Migration revision mismatch: expected {expected_revision} got {migration_revision}"
        )

    _run_migration(migrate_cmd, migration_revision)

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
    parser.add_argument(
        "--migrate-cmd",
        default=None,
        help="Optional migration command executed before applying pack; use {revision} placeholder.",
    )
    args = parser.parse_args()

    out_file = apply_seed_pack(
        Path(args.pack_dir),
        args.migration_revision,
        Path(args.output_dir),
        migrate_cmd=args.migrate_cmd,
    )
    print(json.dumps({"output": str(out_file), "sha256": _stable_sha256(out_file)}))


if __name__ == "__main__":
    main()
