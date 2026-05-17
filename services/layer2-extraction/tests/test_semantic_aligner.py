"""Unit tests for layer2_extraction.alignment.semantic_aligner.SemanticAligner."""

from __future__ import annotations

from layer2_extraction.alignment.semantic_aligner import SemanticAligner


class TestNormalizeName:
    def test_lowercases_input(self):
        a = SemanticAligner()
        assert a._normalize_name("HELLO WORLD") == "hello world"

    def test_removes_punctuation(self):
        a = SemanticAligner()
        result = a._normalize_name("hello, world!")
        assert "," not in result
        assert "!" not in result

    def test_replaces_hyphens_with_spaces(self):
        a = SemanticAligner()
        result = a._normalize_name("real-time processing")
        assert "-" not in result
        assert "real" in result
        assert "time" in result
        assert "processing" in result

    def test_strips_leading_trailing_whitespace(self):
        a = SemanticAligner()
        result = a._normalize_name("  hello  ")
        assert result == result.strip()

    def test_empty_string_returns_empty(self):
        a = SemanticAligner()
        assert a._normalize_name("") == ""

    def test_already_normalized_unchanged(self):
        a = SemanticAligner()
        result = a._normalize_name("hello world")
        assert "hello" in result
        assert "world" in result


class _FakeEntity:
    """Minimal entity stub for cache key tests."""
    def __init__(self, name: str, description: str, entity_type: str = "Capability"):
        self.name = name
        self.description = description
        self.__class__ = type(entity_type, (), {"__name__": entity_type})  # type: ignore[assignment]


class _Cap:
    def __init__(self, name: str, description: str = "A capability"):
        self.name = name
        self.description = description


class _UC:
    def __init__(self, name: str, description: str = "A use case"):
        self.name = name
        self.description = description


class TestComputeCacheKey:
    def test_same_inputs_produce_same_key(self):
        a = SemanticAligner()
        e = _Cap("AI Processing", "Automates tasks")
        k1 = a._compute_cache_key(e)
        k2 = a._compute_cache_key(e)
        assert k1 == k2

    def test_different_names_produce_different_keys(self):
        a = SemanticAligner()
        k1 = a._compute_cache_key(_Cap("AI Processing"))
        k2 = a._compute_cache_key(_Cap("ML Processing"))
        assert k1 != k2

    def test_different_entity_types_produce_different_keys(self):
        a = SemanticAligner()
        k1 = a._compute_cache_key(_Cap("Processing"))
        k2 = a._compute_cache_key(_UC("Processing"))
        assert k1 != k2

    def test_different_descriptions_produce_different_keys(self):
        a = SemanticAligner()
        k1 = a._compute_cache_key(_Cap("Processing", "desc A"))
        k2 = a._compute_cache_key(_Cap("Processing", "desc B"))
        assert k1 != k2

    def test_key_is_a_string(self):
        a = SemanticAligner()
        key = a._compute_cache_key(_Cap("Processing"))
        assert isinstance(key, str)
        assert len(key) > 0
