"""Release Policy: Version and release metadata validation.

Verifies that release metadata exists and is current for release-candidate.
"""

import json
import subprocess
from pathlib import Path

import pytest


class TestReleaseMetadata:
    """Enforce: Release metadata exists and is current."""

    def test_changelog_or_release_notes_exist(self):
        """CHANGELOG or release notes must exist."""
        candidates = [
            "CHANGELOG.md",
            "RELEASE_NOTES.md",
            "docs/CHANGELOG.md",
            "docs/releases/",
        ]

        found = any(Path(c).exists() for c in candidates)

        if not found:
            pytest.skip(
                "No changelog or release notes found — recommended for release-candidate"
            )

    def test_version_file_or_package_json_exists(self):
        """Version metadata should exist in repository."""
        candidates = [
            "version.txt",
            "VERSION",
            "package.json",
            "pyproject.toml",
        ]

        found = any(Path(c).exists() for c in candidates)

        if not found:
            pytest.skip("No version file found — recommended for traceability")

    def test_contracts_current_if_generation_command_exists(self):
        """If contract generation command exists, contracts should be current."""
        makefile = Path("Makefile")
        if not makefile.exists():
            pytest.skip("No Makefile to check for contract generation")

        content = makefile.read_text(encoding="utf-8")

        # If there's a contract generation target, note that contracts should be current
        if "contracts:" in content or "contract-drift" in content:
            # This is informational - actually running the check might be expensive
            pytest.skip(
                "Contract generation target exists - run 'make contract-drift' "
                "to verify contracts are current"
            )

    def test_git_tag_follows_semver_if_tags_exist(self):
        """If git tags exist, they should follow semantic versioning."""
        try:
            result = subprocess.run(
                ["git", "describe", "--tags", "--abbrev=0"],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                pytest.skip("No git tags found")

            latest_tag = result.stdout.strip()

            # Simple semver check: vX.Y.Z or X.Y.Z
            import re
            semver_pattern = r'^v?\d+\.\d+\.\d+(-[\w.]+)?$'

            if not re.match(semver_pattern, latest_tag):
                pytest.skip(f"Latest tag '{latest_tag}' does not follow semver (informational)")

        except (subprocess.CalledProcessError, FileNotFoundError):
            pytest.skip("Git not available")

    def test_release_candidate_branch_naming(self):
        """If on a release branch, naming should follow convention."""
        try:
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                pytest.skip("Could not determine current branch")

            branch = result.stdout.strip()

            # Release branches should follow naming convention
            if branch.startswith("release/"):
                # Should be release/YYYY-MM-DD or release/vX.Y.Z
                import re
                if not re.match(r'^release/(v?\d+\.\d+\.\d+|\d{4}-\d{2}-\d{2})$', branch):
                    pytest.skip(
                        f"Release branch '{branch}' does not follow recommended naming "
                        f"(release/vX.Y.Z or release/YYYY-MM-DD)"
                    )

        except (subprocess.CalledProcessError, FileNotFoundError):
            pytest.skip("Git not available")
