"""Semantic chunker for Layer 2 extraction."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Chunk:
    """A text chunk with positional metadata."""

    content: str
    start_idx: int
    end_idx: int
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.content or not self.content.strip():
            raise ValueError("Chunk content cannot be empty")


class SemanticChunker:
    """Chunk Markdown into semantically meaningful segments."""

    DEFAULT_CHUNK_SIZE = 2000
    DEFAULT_CHUNK_OVERLAP = 200

    def __init__(
        self,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
        preserve_headers: bool = True,
    ) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.preserve_headers = preserve_headers

    # ------------------------------------------------------------------
    # Pre-processing
    # ------------------------------------------------------------------

    def _preprocess(self, text: str) -> str:
        """Normalize whitespace and line endings."""
        text = text.replace("\r\n", "\n")
        text = re.sub(r"\n{4,}", "\n\n\n", text)
        return text.strip()

    # ------------------------------------------------------------------
    # Header splitting
    # ------------------------------------------------------------------

    def _split_by_headers(self, text: str) -> list[dict[str, Any]]:
        """Split text into sections based on Markdown headers."""
        lines = text.split("\n")
        sections: list[dict[str, Any]] = []
        current_lines: list[str] = []
        current_header = ""
        current_level = 0

        def _flush():
            content = "\n".join(current_lines).strip()
            if content or current_header:
                sections.append(
                    {
                        "header": current_header,
                        "level": current_level,
                        "content": content,
                    }
                )

        for line in lines:
            m = re.match(r"^(#{1,6})\s+(.*)$", line)
            if m:
                _flush()
                current_header = m.group(2).strip()
                current_level = len(m.group(1))
                current_lines = []
            else:
                current_lines.append(line)

        _flush()
        # If no headers found, return single section
        if not sections:
            sections.append({"header": "", "level": 0, "content": text.strip()})
        return sections

    # ------------------------------------------------------------------
    # Overlap budget
    # ------------------------------------------------------------------

    def _get_overlap_paras(self, paras: list[str], budget: int) -> list[str]:
        """Select paragraphs that fit within the overlap budget."""
        result: list[str] = []
        total = 0
        for p in paras:
            # +2 for the "\n\n" separator
            needed = len(p) + (2 if result else 0)
            if total + needed > budget:
                break
            result.append(p)
            total += needed
        return result

    # ------------------------------------------------------------------
    # Main chunking
    # ------------------------------------------------------------------

    def chunk_text(self, text: str, source_url: str | None = None) -> list[Chunk]:
        """Split text into chunks."""
        text = self._preprocess(text)
        if not text:
            return []

        sections = self._split_by_headers(text)
        chunks: list[Chunk] = []
        global_idx = 0

        for section in sections:
            header = section["header"]
            level = section["level"]
            content = section["content"]

            if not content:
                # Header-only section: create a tiny chunk
                chunk_text = f"{'#' * level} {header}".strip() if header else ""
                if chunk_text:
                    end_idx = global_idx + len(chunk_text)
                    chunks.append(
                        Chunk(
                            content=chunk_text,
                            start_idx=global_idx,
                            end_idx=end_idx,
                            metadata={
                                "section_header": header,
                                "header_level": level,
                                "source_url": source_url,
                            },
                        )
                    )
                    global_idx = end_idx
                continue

            # Build paragraphs for this section
            paras = content.split("\n\n")
            header_prefix = f"{'#' * level} {header}\n\n" if header and self.preserve_headers else ""

            current_paras: list[str] = []
            current_len = len(header_prefix)

            def _flush_chunk(overlap_paras: list[str] | None = None):
                nonlocal current_paras, current_len, global_idx
                body = "\n\n".join(current_paras)
                chunk_text = header_prefix + body if header_prefix else body
                end_idx = global_idx + len(chunk_text)
                chunks.append(
                    Chunk(
                        content=chunk_text,
                        start_idx=global_idx,
                        end_idx=end_idx,
                        metadata={
                            "section_header": header,
                            "header_level": level,
                            "source_url": source_url,
                        },
                    )
                )
                global_idx = end_idx
                # Start next chunk with overlap
                current_paras = list(overlap_paras) if overlap_paras else []
                current_len = len(header_prefix) + sum(len(p) + 2 for p in current_paras)
                if current_paras:
                    current_len -= 2  # no separator before first

            for para in paras:
                para_len = len(para) + (2 if current_paras else 0)
                if current_len + para_len > self.chunk_size and current_paras:
                    # Determine overlap for next chunk
                    overlap = self._get_overlap_paras(current_paras, self.chunk_overlap)
                    _flush_chunk(overlap)

                if not current_paras:
                    current_len = len(header_prefix) + len(para)
                else:
                    current_len += len(para) + 2
                current_paras.append(para)

            if current_paras:
                _flush_chunk()

        return chunks


# ------------------------------------------------------------------
# Convenience function
# ------------------------------------------------------------------


def chunk_markdown(
    text: str,
    source_url: str | None = None,
    chunk_size: int = SemanticChunker.DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = SemanticChunker.DEFAULT_CHUNK_OVERLAP,
) -> list[Chunk]:
    """Chunk Markdown text using default semantic chunker settings."""
    chunker = SemanticChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return chunker.chunk_text(text, source_url=source_url)
