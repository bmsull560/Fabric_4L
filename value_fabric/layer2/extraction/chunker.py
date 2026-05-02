"""Semantic chunking for document preprocessing.

Stage 1 of the extraction pipeline: splits Markdown documents into
semantically meaningful chunks while preserving context.
"""

import re
from dataclasses import dataclass


@dataclass
class Chunk:
    """A single semantic chunk of text.

    Attributes:
        content: The text content of the chunk
        start_idx: Character index in original document
        end_idx: Character index in original document
        metadata: Additional context (headers, section type, etc.)
    """

    content: str
    start_idx: int
    end_idx: int
    metadata: dict

    def __post_init__(self):
        """Validate chunk after creation."""
        if not self.content.strip():
            raise ValueError("Chunk content cannot be empty")


class SemanticChunker:
    """Chunk documents semantically while preserving structure.

    Uses a hybrid approach:
    1. Split by headers first (preserves document structure)
    2. Within sections, split by character count with overlap
    3. Preserve paragraph boundaries when possible
    """

    def __init__(
        self, chunk_size: int = 2000, chunk_overlap: int = 200, preserve_headers: bool = True
    ):
        """Initialize chunker with configuration.

        Args:
            chunk_size: Target size in characters per chunk
            chunk_overlap: Overlap between chunks in characters
            preserve_headers: Whether to include section headers in each chunk
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.preserve_headers = preserve_headers

    def chunk_text(self, text: str, source_url: str = "") -> list[Chunk]:
        """Split text into semantic chunks.

        Args:
            text: Raw Markdown text to chunk
            source_url: Source URL for provenance

        Returns:
            List of Chunk objects with metadata
        """
        # Preprocess: normalize whitespace but preserve structure
        text = self._preprocess(text)

        # Split by headers first (structure-preserving)
        sections = self._split_by_headers(text)

        chunks = []
        for section in sections:
            section_chunks = self._chunk_section(section, source_url)
            chunks.extend(section_chunks)

        return chunks

    def _preprocess(self, text: str) -> str:
        """Clean and normalize text while preserving structure."""
        # Normalize line endings
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        # Remove excessive blank lines (keep max 2)
        text = re.sub(r"\n{4,}", "\n\n\n", text)

        # Trim leading/trailing whitespace
        text = text.strip()

        return text

    def _split_by_headers(self, text: str) -> list[dict]:
        """Split document into sections by Markdown headers.

        Returns list of dicts with:
        - header: The header line
        - level: Header level (# to ######)
        - content: Content under this header
        """
        # Match headers: # Header, ## Header, etc.
        header_pattern = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)

        sections = []
        current_pos = 0
        current_header = {"text": "", "level": 0}

        for match in header_pattern.finditer(text):
            # Add previous section
            if current_pos < match.start():
                section_text = text[current_pos : match.start()].strip()
                if section_text:
                    sections.append(
                        {
                            "header": current_header["text"],
                            "level": current_header["level"],
                            "content": section_text,
                        }
                    )

            # Update current header
            hashes = match.group(1)
            header_text = match.group(2)
            current_header = {"text": header_text, "level": len(hashes)}
            current_pos = match.end()

        # Add final section
        if current_pos < len(text):
            final_section = text[current_pos:].strip()
            if final_section:
                sections.append(
                    {
                        "header": current_header["text"],
                        "level": current_header["level"],
                        "content": final_section,
                    }
                )

        return sections

    def _chunk_section(self, section: dict, source_url: str) -> list[Chunk]:
        """Chunk a single section into overlapping chunks.

        Preserves paragraph boundaries when possible.
        """
        header = section["header"]
        level = section["level"]
        content = section["content"]

        # Prepend header to content if preserving headers
        if self.preserve_headers and header:
            full_content = f"{'#' * level} {header}\n\n{content}"
        else:
            full_content = content

        # Split into paragraphs
        paragraphs = re.split(r"\n\n+", full_content)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]

        if not paragraphs:
            return []

        chunks = []
        current_chunk = []
        current_length = 0
        start_idx = 0
        char_count = 0

        for para in paragraphs:
            para_length = len(para) + 2  # +2 for \n\n

            # If adding this paragraph exceeds chunk size, finalize current chunk
            if current_length + para_length > self.chunk_size and current_chunk:
                chunk_text = "\n\n".join(current_chunk)
                chunks.append(
                    Chunk(
                        content=chunk_text,
                        start_idx=start_idx,
                        end_idx=start_idx + len(chunk_text),
                        metadata={
                            "section_header": header,
                            "header_level": level,
                            "source_url": source_url,
                            "paragraph_count": len(current_chunk),
                        },
                    )
                )

                # Start new chunk with overlap
                overlap_text = (
                    chunk_text[-self.chunk_overlap :]
                    if len(chunk_text) > self.chunk_overlap
                    else chunk_text
                )
                # Try to get clean paragraph boundary for overlap
                overlap_paras = self._get_overlap_paras(current_chunk, self.chunk_overlap)
                current_chunk = overlap_paras + [para]
                current_length = sum(len(p) + 2 for p in current_chunk)
                start_idx = char_count - len(overlap_text)
            else:
                current_chunk.append(para)
                current_length += para_length

            char_count += para_length

        # Add final chunk
        if current_chunk:
            chunk_text = "\n\n".join(current_chunk)
            chunks.append(
                Chunk(
                    content=chunk_text,
                    start_idx=start_idx,
                    end_idx=start_idx + len(chunk_text),
                    metadata={
                        "section_header": header,
                        "header_level": level,
                        "source_url": source_url,
                        "paragraph_count": len(current_chunk),
                    },
                )
            )

        return chunks

    def _get_overlap_paras(self, paragraphs: list[str], overlap_chars: int) -> list[str]:
        """Get paragraphs that fit within overlap window."""
        overlap_paras = []
        current_len = 0

        # Work backwards from end
        for para in reversed(paragraphs):
            para_len = len(para) + 2
            if current_len + para_len <= overlap_chars:
                overlap_paras.insert(0, para)
                current_len += para_len
            else:
                break

        return overlap_paras


def chunk_markdown(
    markdown: str, source_url: str = "", chunk_size: int = 2000, chunk_overlap: int = 200
) -> list[Chunk]:
    """Convenience function to chunk Markdown text.

    Args:
        markdown: Markdown text to chunk
        source_url: Source URL for provenance tracking
        chunk_size: Target chunk size in characters
        chunk_overlap: Overlap between chunks

    Returns:
        List of semantic chunks with metadata
    """
    chunker = SemanticChunker(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap, preserve_headers=True
    )
    return chunker.chunk_text(markdown, source_url)
