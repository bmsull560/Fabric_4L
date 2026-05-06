from __future__ import annotations

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_PATH = REPO_ROOT / "scripts" / "ci" / "validate-env-contract.ts"
DEV_CHECKER_PATH = REPO_ROOT / "scripts" / "dev" / "check-env.ts"
CONFIG_ENV_DIR = REPO_ROOT / "packages" / "config" / "src" / "env"


def test_env_contract_validator_targets_active_env_examples_and_fails_closed():
    source = VALIDATOR_PATH.read_text(encoding="utf-8")

    assert "../../.env.example" in source
    assert "../../apps/web/.env.example" in source
    assert "../../.env.example" not in source
    assert "../../frontend/.env.example" not in source
    assert "existsSync(filePath)" in source
    assert "Contract file does not exist" in source
    assert "Contract file declares no environment variables" in source


def test_config_env_schema_files_back_declared_package_exports():
    for filename in ("shared.ts", "backend.ts", "frontend.ts", "test.ts"):
        schema_path = CONFIG_ENV_DIR / filename
        assert schema_path.is_file(), f"missing config env schema file: {filename}"
        ignore_check = subprocess.run(
            ["git", "check-ignore", str(schema_path.relative_to(REPO_ROOT))],
            cwd=REPO_ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        assert ignore_check.returncode == 1, ignore_check.stdout

    dev_checker_source = DEV_CHECKER_PATH.read_text(encoding="utf-8")
    assert "../../packages/config/src/env/backend.js" in dev_checker_source
    assert "../../packages/config/src/env/frontend.js" in dev_checker_source
    assert "from \"../packages/config/src/env" not in dev_checker_source


def test_config_package_env_schemas_compile():
    result = subprocess.run(
        ["pnpm", "--dir", "packages/config", "exec", "tsc", "--noEmit"],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode == 0, result.stdout
