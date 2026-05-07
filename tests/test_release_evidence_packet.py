from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest


def _load_module():
    root = Path(__file__).resolve().parents[1]
    module_path = root / "scripts/ci/generate_release_evidence_packet.py"
    spec = importlib.util.spec_from_file_location("generate_release_evidence_packet", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write_manifest(path: Path, release_sha: str) -> None:
    path.write_text(
        "\n".join(
            [
                f'release_candidate_sha: "{release_sha}"',
                'generated_at_utc: "2026-01-01T00:00:00Z"',
                "gates:",
                "  production_like_e2e:",
                "    status: REQUIRES_ENVIRONMENT",
                "    owner: qa-owner",
                "    evidence_uri: null",
                '    acceptance: "Launch journey passes."',
                "  enterprise_sso_oidc:",
                "    status: REQUIRES_ENVIRONMENT",
                "    owner: identity-owner",
                "    evidence_uri: null",
                '    acceptance: "SSO validation complete."',
                "  rollback_restore:",
                "    status: REQUIRES_ENVIRONMENT",
                "    owner: sre-owner",
                "    evidence_uri: null",
                '    acceptance: "Rollback verified."',
                "  telemetry_alerting:",
                "    status: REQUIRES_ENVIRONMENT",
                "    owner: obs-owner",
                "    evidence_uri: null",
                '    acceptance: "Telemetry verified."',
                "  billing_metering:",
                "    status: REQUIRES_ENVIRONMENT",
                "    owner: billing-owner",
                "    evidence_uri: null",
                '    acceptance: "Billing verified."',
                "  performance_smoke:",
                "    status: REQUIRES_ENVIRONMENT",
                "    owner: perf-owner",
                "    evidence_uri: null",
                '    acceptance: "Performance smoke verified."',
                "allowed_statuses:",
                "  - REQUIRES_ENVIRONMENT",
                "  - PASS_WITH_EVIDENCE",
                "  - FAIL",
                "  - WAIVED",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def test_generate_release_evidence_packet_writes_outputs(tmp_path, monkeypatch):
    module = _load_module()
    manifest_path = tmp_path / "manifest.yaml"
    output_dir = tmp_path / "packet"
    release_sha = "abc123"
    _write_manifest(manifest_path, release_sha)

    validator_names = []

    def fake_validate_manifest(_path: Path) -> list[str]:
        return []

    def fake_run_validator(name: str, command: list[str]):
        validator_names.append((name, command))
        return module.ValidatorResult(name=name, passed=True, command=command, detail="ok")

    monkeypatch.setattr(module, "_load_manifest_validator", lambda: fake_validate_manifest)
    monkeypatch.setattr(module, "_run_validator", fake_run_validator)

    exit_code = module.generate_release_evidence_packet(
        manifest_path=manifest_path,
        output_dir=output_dir,
        release_sha=release_sha,
        allow_placeholder_sha=False,
    )

    assert exit_code == 0
    assert len(validator_names) == 5

    packet = json.loads((output_dir / "release-evidence-packet.json").read_text(encoding="utf-8"))
    assert packet["release_sha"] == release_sha
    assert packet["overall_status"] == "PASS"

    summary = (output_dir / "release-evidence-summary.md").read_text(encoding="utf-8")
    assert "Release Evidence Packet" in summary
    assert "Overall status: **PASS**" in summary


def test_generate_release_evidence_packet_fails_on_sha_mismatch(tmp_path):
    module = _load_module()
    manifest_path = tmp_path / "manifest.yaml"
    _write_manifest(manifest_path, "sha-in-manifest")

    with pytest.raises(ValueError, match="does not match release SHA"):
        module.generate_release_evidence_packet(
            manifest_path=manifest_path,
            output_dir=tmp_path / "packet",
            release_sha="different-sha",
            allow_placeholder_sha=False,
        )


def test_generate_release_evidence_packet_returns_nonzero_when_validator_fails(tmp_path, monkeypatch):
    module = _load_module()
    manifest_path = tmp_path / "manifest.yaml"
    output_dir = tmp_path / "packet"
    release_sha = "abc123"
    _write_manifest(manifest_path, release_sha)

    def fake_validate_manifest(_path: Path) -> list[str]:
        return []

    def fake_run_validator(name: str, command: list[str]):
        passed = name != "platform_contract_lint"
        return module.ValidatorResult(name=name, passed=passed, command=command, detail="ok" if passed else "failed")

    monkeypatch.setattr(module, "_load_manifest_validator", lambda: fake_validate_manifest)
    monkeypatch.setattr(module, "_run_validator", fake_run_validator)

    exit_code = module.generate_release_evidence_packet(
        manifest_path=manifest_path,
        output_dir=output_dir,
        release_sha=release_sha,
        allow_placeholder_sha=False,
    )

    packet = json.loads((output_dir / "release-evidence-packet.json").read_text(encoding="utf-8"))
    assert exit_code == 1
    assert packet["overall_status"] == "FAIL"
