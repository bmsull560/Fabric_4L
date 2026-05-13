from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


class CheckReleaseLaunchGovernanceTests(unittest.TestCase):
    def test_release_launch_governance_script_passes_current_checklist(self) -> None:
        root = Path(__file__).resolve().parents[3]
        result = subprocess.run(
            [sys.executable, "scripts/ci/check_release_launch_governance.py"],
            cwd=root,
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
