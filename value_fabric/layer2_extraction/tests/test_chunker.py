"""Tests for semantic chunker (layer2-extraction/src/.../extraction/chunker.py)."""

import importlib
from pathlib import Path

import pytest

# Import the chunker module directly (avoid __init__.py chain that pulls numpy)
_chunker_path = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "layer2_extraction"
    / "extraction"
    / "chunker.py"
)
spec = importlib.util.spec_from_file_location("chunker", _chunker_path)
_chunker_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(_chunker_mod)

Chunk = _chunker_mod.Chunk
SemanticChunker = _chunker_mod.SemanticChunker
chunk_markdown = _chunker_mod.chunk_markdown


# ═══════════════════════════════════════════════════════════════════════════
# Chunk dataclass
# ═══════════════════════════════════════════════════════════════════════════


class TestChunk:
    def test_valid_creation(self):
        c = Chunk(content="Hello world", start_idx=0, end_idx=11, metadata={})
        assert c.content == "Hello world"

    def test_empty_content_raises(self):
        with pytest.raises(ValueError, match="empty"):
            Chunk(content="   ", start_idx=0, end_idx=3, metadata={})

    def test_whitespace_only_raises(self):
        with pytest.raises(ValueError, match="empty"):
            Chunk(content="\n\n", start_idx=0, end_idx=2, metadata={})


# ═══════════════════════════════════════════════════════════════════════════
# SemanticChunker
# ═══════════════════════════════════════════════════════════════════════════


class TestSemanticChunker:
    def test_default_config(self):
        chunker = SemanticChunker()
        assert chunker.chunk_size == 2000
        assert chunker.chunk_overlap == 200
        assert chunker.preserve_headers is True

    def test_custom_config(self):
        chunker = SemanticChunker(chunk_size=500, chunk_overlap=50, preserve_headers=False)
        assert chunker.chunk_size == 500
        assert chunker.chunk_overlap == 50


class TestPreprocess:
    def setup_method(self):
        self.chunker = SemanticChunker()

    def test_normalizes_crlf(self):
        result = self.chunker._preprocess("Hello\r\nWorld")
        assert "\r" not in result
        assert result == "Hello\nWorld"

    def test_collapses_excessive_blank_lines(self):
        text = "Para 1\n\n\n\n\n\nPara 2"
        result = self.chunker._preprocess(text)
        assert "\n\n\n\n" not in result

    def test_strips_whitespace(self):
        result = self.chunker._preprocess("  Hello  ")
        assert result == "Hello"


class TestSplitByHeaders:
    def setup_method(self):
        self.chunker = SemanticChunker()

    def test_no_headers(self):
        text = "Just a paragraph of text."
        sections = self.chunker._split_by_headers(text)
        assert len(sections) == 1
        assert sections[0]["header"] == ""
        assert sections[0]["level"] == 0

    def test_single_header(self):
        text = "# Title\n\nParagraph under title."
        sections = self.chunker._split_by_headers(text)
        assert len(sections) == 1
        assert sections[0]["header"] == "Title"
        assert sections[0]["level"] == 1

    def test_multiple_headers(self):
        text = "# H1\n\nContent 1\n\n## H2\n\nContent 2\n\n### H3\n\nContent 3"
        sections = self.chunker._split_by_headers(text)
        assert len(sections) == 3
        assert sections[0]["header"] == "H1"
        assert sections[1]["header"] == "H2"
        assert sections[1]["level"] == 2
        assert sections[2]["header"] == "H3"
        assert sections[2]["level"] == 3

    def test_content_before_first_header(self):
        text = "Preamble text.\n\n# Title\n\nBody."
        sections = self.chunker._split_by_headers(text)
        assert len(sections) == 2
        assert sections[0]["header"] == ""
        assert "Preamble" in sections[0]["content"]


class TestChunkText:
    def test_short_text_single_chunk(self):
        chunker = SemanticChunker(chunk_size=5000)
        text = "# Title\n\nShort paragraph."
        chunks = chunker.chunk_text(text)
        assert len(chunks) == 1
        assert "Title" in chunks[0].content

    def test_source_url_in_metadata(self):
        chunker = SemanticChunker()
        chunks = chunker.chunk_text("# Test\n\nContent here.", source_url="https://example.com")
        assert chunks[0].metadata["source_url"] == "https://example.com"

    def test_long_text_multiple_chunks(self):
        chunker = SemanticChunker(chunk_size=100, chunk_overlap=20)
        # Create text long enough to require splitting
        paras = [f"Paragraph {i} with some extra content to fill space." for i in range(20)]
        text = "# Test Section\n\n" + "\n\n".join(paras)
        chunks = chunker.chunk_text(text)
        assert len(chunks) > 1

    def test_preserves_header_in_chunks(self):
        chunker = SemanticChunker(chunk_size=100, chunk_overlap=20, preserve_headers=True)
        paras = [f"Paragraph {i} content." for i in range(10)]
        text = "## My Section\n\n" + "\n\n".join(paras)
        chunks = chunker.chunk_text(text)
        # First chunk should contain the header
        assert "## My Section" in chunks[0].content

    def test_metadata_includes_section_info(self):
        chunker = SemanticChunker()
        text = "## Analysis\n\nSome analysis content here."
        chunks = chunker.chunk_text(text)
        assert chunks[0].metadata["section_header"] == "Analysis"
        assert chunks[0].metadata["header_level"] == 2

    def test_empty_text_returns_empty(self):
        chunker = SemanticChunker()
        chunks = chunker.chunk_text("")
        assert chunks == []

    def test_chunk_indices_are_nonnegative(self):
        chunker = SemanticChunker(chunk_size=200, chunk_overlap=50)
        text = "# Title\n\n" + "\n\n".join(
            [f"Paragraph {i} with some content to make this longer." for i in range(15)]
        )
        chunks = chunker.chunk_text(text)
        for chunk in chunks:
            assert chunk.start_idx >= 0
            assert chunk.end_idx >= chunk.start_idx


class TestGetOverlapParas:
    def setup_method(self):
        self.chunker = SemanticChunker()

    def test_returns_paragraphs_within_budget(self):
        paras = ["Short.", "Medium length.", "A longer paragraph with more text."]
        result = self.chunker._get_overlap_paras(paras, 50)
        total_len = sum(len(p) + 2 for p in result)
        assert total_len <= 50

    def test_empty_paragraphs(self):
        result = self.chunker._get_overlap_paras([], 100)
        assert result == []

    def test_single_paragraph(self):
        result = self.chunker._get_overlap_paras(["Hello"], 100)
        assert result == ["Hello"]


# ═══════════════════════════════════════════════════════════════════════════
# Convenience function
# ═══════════════════════════════════════════════════════════════════════════


class TestChunkMarkdown:
    def test_basic_usage(self):
        chunks = chunk_markdown("# Hello\n\nWorld", source_url="https://test.com")
        assert len(chunks) >= 1
        assert chunks[0].metadata["source_url"] == "https://test.com"

    def test_custom_parameters(self):
        text = "# Title\n\n" + "\n\n".join([f"Para {i}." for i in range(50)])
        chunks = chunk_markdown(text, chunk_size=100, chunk_overlap=10)
        assert len(chunks) > 1
