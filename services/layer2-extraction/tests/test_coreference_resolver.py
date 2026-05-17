"""Unit tests for CoreferenceResolver.

Covers the three required scenarios from the spec:
  1. No duplicates — passthrough (list unchanged)
  2. Exact duplicates — merge provenance, return single canonical entity
  3. Partial matches (same name, different type) — no merge, both kept

Tests use plain dicts as entities (the resolver supports both dicts and
attribute-style objects).
"""

from __future__ import annotations

import pytest

from layer2_extraction.coreference.coreference_resolver import CoreferenceResolver


@pytest.fixture()
def resolver() -> CoreferenceResolver:
    return CoreferenceResolver()


# ── 1. No duplicates — passthrough ────────────────────────────────────────


class TestNoduplicatesPassthrough:
    def test_empty_list_returns_empty(self, resolver: CoreferenceResolver) -> None:
        assert resolver.resolve([]) == []

    def test_single_entity_returned_unchanged(self, resolver: CoreferenceResolver) -> None:
        entity = {"name": "Acme Corp", "entity_type": "organization"}
        result = resolver.resolve([entity])
        assert result == [entity]

    def test_distinct_entities_all_returned(self, resolver: CoreferenceResolver) -> None:
        entities = [
            {"name": "Acme Corp", "entity_type": "organization"},
            {"name": "John Smith", "entity_type": "person"},
            {"name": "Q4 Revenue", "entity_type": "metric"},
        ]
        result = resolver.resolve(entities)
        assert len(result) == 3

    def test_same_name_different_type_both_kept(self, resolver: CoreferenceResolver) -> None:
        """Partial match: same name, different entity_type — no deduplication."""
        entities = [
            {"name": "Acme", "entity_type": "organization"},
            {"name": "Acme", "entity_type": "product"},
        ]
        result = resolver.resolve(entities)
        assert len(result) == 2

    def test_same_type_different_name_both_kept(self, resolver: CoreferenceResolver) -> None:
        entities = [
            {"name": "Acme Corp", "entity_type": "organization"},
            {"name": "Beta Inc", "entity_type": "organization"},
        ]
        result = resolver.resolve(entities)
        assert len(result) == 2

    def test_entities_without_identity_fields_passed_through(
        self, resolver: CoreferenceResolver
    ) -> None:
        """Entities with no name/entity_type are passed through without deduplication."""
        entities = [{"value": 42}, {"value": 99}]
        result = resolver.resolve(entities)
        assert len(result) == 2


# ── 2. Exact duplicates — merge provenance ────────────────────────────────


class TestExactDuplicateMerge:
    def test_exact_duplicate_removed(self, resolver: CoreferenceResolver) -> None:
        entities = [
            {"name": "Acme Corp", "entity_type": "organization"},
            {"name": "Acme Corp", "entity_type": "organization"},
        ]
        result = resolver.resolve(entities)
        assert len(result) == 1

    def test_case_insensitive_deduplication(self, resolver: CoreferenceResolver) -> None:
        entities = [
            {"name": "Acme Corp", "entity_type": "Organization"},
            {"name": "ACME CORP", "entity_type": "organization"},
            {"name": "acme corp", "entity_type": "ORGANIZATION"},
        ]
        result = resolver.resolve(entities)
        assert len(result) == 1

    def test_whitespace_normalised_before_comparison(
        self, resolver: CoreferenceResolver
    ) -> None:
        entities = [
            {"name": "Acme  Corp", "entity_type": "organization"},
            {"name": "Acme Corp", "entity_type": "organization"},
        ]
        result = resolver.resolve(entities)
        assert len(result) == 1

    def test_canonical_is_first_occurrence(self, resolver: CoreferenceResolver) -> None:
        first = {"name": "Acme Corp", "entity_type": "organization", "source": "doc-1"}
        second = {"name": "Acme Corp", "entity_type": "organization", "source": "doc-2"}
        result = resolver.resolve([first, second])
        assert result[0]["source"] == "doc-1"

    def test_provenance_merged_from_duplicate(self, resolver: CoreferenceResolver) -> None:
        canonical = {
            "name": "Acme Corp",
            "entity_type": "organization",
            "provenance": ["doc-1"],
        }
        duplicate = {
            "name": "Acme Corp",
            "entity_type": "organization",
            "provenance": ["doc-2"],
        }
        result = resolver.resolve([canonical, duplicate])
        assert len(result) == 1
        assert "doc-1" in result[0]["provenance"]
        assert "doc-2" in result[0]["provenance"]

    def test_provenance_merged_from_multiple_duplicates(
        self, resolver: CoreferenceResolver
    ) -> None:
        entities = [
            {"name": "Acme", "entity_type": "org", "provenance": ["a"]},
            {"name": "Acme", "entity_type": "org", "provenance": ["b"]},
            {"name": "Acme", "entity_type": "org", "provenance": ["c"]},
        ]
        result = resolver.resolve(entities)
        assert len(result) == 1
        assert set(result[0]["provenance"]) == {"a", "b", "c"}

    def test_no_provenance_field_no_error(self, resolver: CoreferenceResolver) -> None:
        """Merging entities without provenance fields must not raise."""
        entities = [
            {"name": "Acme", "entity_type": "org"},
            {"name": "Acme", "entity_type": "org"},
        ]
        result = resolver.resolve(entities)
        assert len(result) == 1


# ── 3. Partial matches — no merge ─────────────────────────────────────────


class TestPartialMatchNoMerge:
    def test_same_name_different_type_independent(
        self, resolver: CoreferenceResolver
    ) -> None:
        entities = [
            {"name": "Velocity", "entity_type": "metric"},
            {"name": "Velocity", "entity_type": "product"},
        ]
        result = resolver.resolve(entities)
        assert len(result) == 2
        types = {e["entity_type"] for e in result}
        assert types == {"metric", "product"}

    def test_different_name_same_type_independent(
        self, resolver: CoreferenceResolver
    ) -> None:
        entities = [
            {"name": "Alpha", "entity_type": "organization"},
            {"name": "Beta", "entity_type": "organization"},
        ]
        result = resolver.resolve(entities)
        assert len(result) == 2

    def test_mixed_batch_deduplicates_only_exact_matches(
        self, resolver: CoreferenceResolver
    ) -> None:
        entities = [
            {"name": "Acme", "entity_type": "org"},       # canonical
            {"name": "Acme", "entity_type": "org"},       # duplicate → merged
            {"name": "Acme", "entity_type": "product"},   # different type → kept
            {"name": "Beta", "entity_type": "org"},       # different name → kept
        ]
        result = resolver.resolve(entities)
        assert len(result) == 3


# ── 4. are_semantically_equivalent ────────────────────────────────────────


class TestAreSemanticalllyEquivalent:
    def test_always_returns_false(self, resolver: CoreferenceResolver) -> None:
        e1 = {"name": "Acme", "entity_type": "org"}
        e2 = {"name": "Acme Corp", "entity_type": "org"}
        assert resolver.are_semantically_equivalent(e1, e2) is False

    def test_identical_entities_still_false(self, resolver: CoreferenceResolver) -> None:
        e = {"name": "Acme", "entity_type": "org"}
        assert resolver.are_semantically_equivalent(e, e) is False
