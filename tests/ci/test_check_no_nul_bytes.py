from __future__ import annotations

from pathlib import Path

from scripts.ci.check_no_nul_bytes import files_with_nul


def test_files_with_nul_flags_only_corrupted_files(tmp_path: Path) -> None:
    good = tmp_path / "good.py"
    bad = tmp_path / "bad.py"

    good.write_text("print('ok')\n", encoding="utf-8")
    bad.write_bytes(b"print('bad')\n\x00")

    offenders = files_with_nul([good, bad], tmp_path)

    assert offenders == ["bad.py"]
