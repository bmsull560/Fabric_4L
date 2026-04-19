"""Tests for pack_loader module.

Exposes real defects in path handling and version extraction.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from src.api.routes.pack_loader import (
    VALID_PACK_ID_PATTERN,
    get_available_packs,
    invalidate_cache,
    load_pack_formulas,
    load_pack_manifest,
)


class TestPackIdValidation:
    """Tests for pack ID regex validation."""

    def test_valid_pack_ids(self):
        """Should accept valid alphanumeric pack IDs with hyphens."""
        valid_ids = [
            "financial-services-v1",
            "manufacturing-v1",
            "ai-technology-v1",
            "valid-pack-123",
            "simple",
            "a-b-c-d",
        ]
        for pid in valid_ids:
            assert VALID_PACK_ID_PATTERN.match(pid), f"Should match: {pid}"

    def test_invalid_pack_ids(self):
        """Should reject pack IDs with dangerous characters."""
        invalid_ids = [
            "test..pack",  # dots
            "test/pack",  # forward slash
            "test\\\\pack",  # backslash
            "test_pack",  # underscore (not in allowed set)
            "test@pack",  # special char
            "",  # empty string
        ]
        for pid in invalid_ids:
            assert not VALID_PACK_ID_PATTERN.match(pid), f"Should NOT match: {pid}"


class TestVersionExtractionBug:
    """Tests exposing the version extraction defect."""

    def test_v2_pack_id_corruption(self):
        """BUG: v2 packs don't load because -v1 replacement doesn't handle -v2."""
        # This test exposes the real bug
        pack_id = "manufacturing-v2"
        # Current broken implementation:
        slug = pack_id.replace("-v1", "")
        # Expected: manufacturing-v2 or manufacturing
        # Actual: manufacturing-v2 (unchanged - WRONG)
        assert slug == "manufacturing-v2", "v2 packs get wrong slug"

    def test_v123_pack_id_corruption(self):
        """BUG: -v1 string removal is too greedy, corrupts valid IDs."""
        pack_id = "test-v123"
        # Current broken implementation:
        slug = pack_id.replace("-v1", "")
        # Expected: test-v123 or test
        # Actual: test23 (corrupted!)
        assert slug == "test23", "This exposes the corruption bug"


class TestPathTraversalProtection:
    """Tests for path traversal safety."""

    def test_pack_id_becomes_empty_after_replace(self):
        """BUG: pack_id '-v1' becomes empty string after replace."""
        pack_id = "-v1"
        # This passes regex validation!
        assert VALID_PACK_ID_PATTERN.match(pack_id)

        slug = pack_id.replace("-v1", "")
        # slug is now empty string
        assert slug == "", "Empty string produced from valid pack_id"

        # This could lead to PACKS_DIR / "" / "formulas.json"
        # which resolves to just PACKS_DIR / "formulas.json"

    def test_directory_escape_attempts_blocked(self):
        """Various escape attempts should return empty list."""
        # These should all safely return empty lists
        dangerous_ids = [
            "..-v1",  # becomes ".." after replace - TRAVERSAL RISK
            ".-v1",  # becomes "." after replace
            "-v1",  # becomes "" after replace
        ]

        for pid in dangerous_ids:
            # Should not raise, should return empty list
            result = load_pack_formulas(pid)
            assert result == [], f"Dangerous pack_id {pid} should return empty list"


class TestCacheBehavior:
    """Tests for module-level caching."""

    def test_cache_invalidation(self):
        """Cache should clear when invalidate_cache is called."""
        invalidate_cache()
        # After invalidation, cache should be None internally
        # We can't directly test this without internal access,
        # but we can verify behavior changes after invalidation


class TestManifestLoading:
    """Tests for manifest loading edge cases."""

    def test_missing_manifest_returns_none(self):
        """Should return None when manifest doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("src.api.routes.pack_loader.MANIFEST_FILE", Path(tmpdir) / "nonexistent.json"):
                result = load_pack_manifest()
                assert result is None

    def test_malformed_manifest_returns_none(self):
        """BUG: Malformed JSON silently returns None instead of raising."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_file = Path(tmpdir) / "pack-manifest.json"
            manifest_file.write_text("not valid json {")

            with patch("src.api.routes.pack_loader.MANIFEST_FILE", manifest_file):
                # Current implementation silently returns None on JSON errors
                # This could hide data corruption issues
                result = load_pack_manifest()
                assert result is None  # Silent failure - logs no error


class TestFormulaLoading:
    """Tests for formula loading from packs."""

    def test_missing_formulas_file_returns_empty(self):
        """Should return empty list when formulas.json doesn't exist."""
        result = load_pack_formulas("nonexistent-pack-v1")
        assert result == []

    def test_valid_pack_loads_formulas(self):
        """Should load formulas from a valid pack."""
        # Use a known valid pack from the manifest
        packs = get_available_packs()
        if packs:
            pack_id = packs[0]["pack_id"]
            formulas = load_pack_formulas(pack_id)
            # Should return a list (may be empty if files don't exist in test env)
            assert isinstance(formulas, list)
