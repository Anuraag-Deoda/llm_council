"""
Chunking service for splitting documents into smaller, embeddable chunks.
"""
import logging
import re
from dataclasses import dataclass
from typing import List, Optional, Tuple

import tiktoken

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class TextChunk:
    """Represents a chunk of text from a document."""
    content: str
    chunk_index: int
    start_char: int
    end_char: int
    token_count: int
    section_title: Optional[str] = None


class ChunkingService:
    """
    Service for splitting documents into semantic chunks.

    Uses tiktoken for accurate token counting and implements
    semantic-aware chunking that respects document structure.
    """

    # Patterns for detecting section boundaries
    SECTION_PATTERNS = [
        r'^#{1,6}\s+.+$',  # Markdown headings
        r'^[A-Z][^.!?]*[.!?]$',  # Sentence-like lines starting with capital
        r'^\d+\.\s+.+$',  # Numbered lists
        r'^[-*]\s+.+$',  # Bullet points
    ]

    def __init__(
        self,
        chunk_size: int = None,
        chunk_overlap: int = None,
        encoding_name: str = "cl100k_base"
    ):
        """
        Initialize the chunking service.

        Args:
            chunk_size: Target chunk size in tokens (default from settings)
            chunk_overlap: Overlap between chunks in tokens (default from settings)
            encoding_name: Tiktoken encoding name
        """
        self.chunk_size = chunk_size or settings.rag_chunk_size
        self.chunk_overlap = chunk_overlap or settings.rag_chunk_overlap
        self.encoding = tiktoken.get_encoding(encoding_name)

    def count_tokens(self, text: str) -> int:
        """
        Count the number of tokens in text.

        Args:
            text: Text to count tokens for

        Returns:
            Number of tokens
        """
        return len(self.encoding.encode(text))

    def chunk_document(
        self,
        content: str,
        preserve_sections: bool = True
    ) -> List[TextChunk]:
        """
        Split document content into chunks.

        Args:
            content: Full document content
            preserve_sections: Try to keep sections together

        Returns:
            List of TextChunk objects
        """
        if not content or not content.strip():
            return []

        # Clean and normalize content
        content = self._normalize_content(content)

        if preserve_sections:
            chunks = self._chunk_with_sections(content)
        else:
            chunks = self._chunk_simple(content)

        return chunks

    def _normalize_content(self, content: str) -> str:
        """Normalize whitespace and clean content."""
        # Replace multiple newlines with double newline
        content = re.sub(r'\n{3,}', '\n\n', content)
        # Replace multiple spaces with single space
        content = re.sub(r' {2,}', ' ', content)
        # Strip trailing whitespace from lines
        lines = [line.rstrip() for line in content.split('\n')]
        return '\n'.join(lines)

    def _chunk_with_sections(self, content: str) -> List[TextChunk]:
        """
        Chunk content while trying to preserve section boundaries.
        """
        # Split into paragraphs
        paragraphs = self._split_into_paragraphs(content)

        chunks = []
        current_chunk_parts = []
        current_tokens = 0
        current_section = None
        chunk_start = 0

        for para_text, para_start, para_end in paragraphs:
            para_tokens = self.count_tokens(para_text)

            # Check if this paragraph is a section header
            section_title = self._extract_section_title(para_text)
            if section_title:
                current_section = section_title

            # If adding this paragraph would exceed chunk size
            if current_tokens + para_tokens > self.chunk_size and current_chunk_parts:
                # Save current chunk
                chunk_content = '\n\n'.join(current_chunk_parts)
                chunks.append(TextChunk(
                    content=chunk_content,
                    chunk_index=len(chunks),
                    start_char=chunk_start,
                    end_char=para_start,
                    token_count=current_tokens,
                    section_title=current_section,
                ))

                # Start new chunk with overlap
                overlap_parts, overlap_tokens = self._get_overlap(
                    current_chunk_parts, self.chunk_overlap
                )
                current_chunk_parts = overlap_parts + [para_text]
                current_tokens = overlap_tokens + para_tokens
                chunk_start = para_start - sum(len(p) + 2 for p in overlap_parts)
            else:
                current_chunk_parts.append(para_text)
                current_tokens += para_tokens

            # Handle very long paragraphs
            if para_tokens > self.chunk_size:
                # Split long paragraph into sentences
                sub_chunks = self._split_long_paragraph(
                    para_text, para_start, current_section, len(chunks)
                )
                if sub_chunks:
                    # Add sub-chunks (skip first if we already added paragraph)
                    for sub_chunk in sub_chunks:
                        sub_chunk.chunk_index = len(chunks)
                        chunks.append(sub_chunk)
                    current_chunk_parts = []
                    current_tokens = 0
                    chunk_start = para_end

        # Don't forget the last chunk
        if current_chunk_parts:
            chunk_content = '\n\n'.join(current_chunk_parts)
            chunks.append(TextChunk(
                content=chunk_content,
                chunk_index=len(chunks),
                start_char=chunk_start,
                end_char=len(content),
                token_count=current_tokens,
                section_title=current_section,
            ))

        # Reindex chunks
        for i, chunk in enumerate(chunks):
            chunk.chunk_index = i

        return chunks

    def _chunk_simple(self, content: str) -> List[TextChunk]:
        """
        Simple chunking without section awareness.
        """
        tokens = self.encoding.encode(content)
        total_tokens = len(tokens)

        if total_tokens <= self.chunk_size:
            return [TextChunk(
                content=content,
                chunk_index=0,
                start_char=0,
                end_char=len(content),
                token_count=total_tokens,
            )]

        chunks = []
        start_token = 0

        while start_token < total_tokens:
            end_token = min(start_token + self.chunk_size, total_tokens)

            # Decode the chunk
            chunk_tokens = tokens[start_token:end_token]
            chunk_content = self.encoding.decode(chunk_tokens)

            # Calculate character positions (approximate)
            if start_token == 0:
                start_char = 0
            else:
                start_char = len(self.encoding.decode(tokens[:start_token]))
            end_char = len(self.encoding.decode(tokens[:end_token]))

            chunks.append(TextChunk(
                content=chunk_content,
                chunk_index=len(chunks),
                start_char=start_char,
                end_char=end_char,
                token_count=len(chunk_tokens),
            ))

            # Move forward with overlap
            start_token = end_token - self.chunk_overlap

        return chunks

    def _split_into_paragraphs(self, content: str) -> List[Tuple[str, int, int]]:
        """
        Split content into paragraphs with character positions.

        Returns:
            List of (paragraph_text, start_char, end_char) tuples
        """
        paragraphs = []
        current_pos = 0

        # Split on double newlines
        for match in re.finditer(r'(.+?)(?:\n\n|\Z)', content, re.DOTALL):
            para_text = match.group(1).strip()
            if para_text:
                start = match.start()
                end = match.end()
                paragraphs.append((para_text, start, end))

        return paragraphs

    def _extract_section_title(self, text: str) -> Optional[str]:
        """Extract section title from text if it's a heading."""
        first_line = text.split('\n')[0].strip()

        # Check for markdown heading
        if first_line.startswith('#'):
            return first_line.lstrip('#').strip()

        # Check for numbered section
        match = re.match(r'^(\d+\.)+\s+(.+)$', first_line)
        if match:
            return match.group(2)

        return None

    def _get_overlap(
        self, parts: List[str], overlap_tokens: int
    ) -> Tuple[List[str], int]:
        """
        Get overlapping text from the end of current chunk.

        Args:
            parts: List of paragraph texts
            overlap_tokens: Target overlap in tokens

        Returns:
            Tuple of (overlap_parts, total_tokens)
        """
        if not parts or overlap_tokens <= 0:
            return [], 0

        overlap_parts = []
        total_tokens = 0

        # Work backwards through parts
        for part in reversed(parts):
            part_tokens = self.count_tokens(part)
            if total_tokens + part_tokens <= overlap_tokens:
                overlap_parts.insert(0, part)
                total_tokens += part_tokens
            else:
                break

        return overlap_parts, total_tokens

    def _split_long_paragraph(
        self,
        text: str,
        start_pos: int,
        section_title: Optional[str],
        base_index: int
    ) -> List[TextChunk]:
        """
        Split a very long paragraph into sentence-based chunks.
        """
        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)

        if len(sentences) <= 1:
            # Can't split further, just return as is
            return []

        chunks = []
        current_sentences = []
        current_tokens = 0
        current_start = start_pos

        for sentence in sentences:
            sentence_tokens = self.count_tokens(sentence)

            if current_tokens + sentence_tokens > self.chunk_size and current_sentences:
                # Save current chunk
                chunk_content = ' '.join(current_sentences)
                chunks.append(TextChunk(
                    content=chunk_content,
                    chunk_index=base_index + len(chunks),
                    start_char=current_start,
                    end_char=current_start + len(chunk_content),
                    token_count=current_tokens,
                    section_title=section_title,
                ))

                current_sentences = [sentence]
                current_tokens = sentence_tokens
                current_start = current_start + len(chunk_content) + 1
            else:
                current_sentences.append(sentence)
                current_tokens += sentence_tokens

        # Last chunk
        if current_sentences:
            chunk_content = ' '.join(current_sentences)
            chunks.append(TextChunk(
                content=chunk_content,
                chunk_index=base_index + len(chunks),
                start_char=current_start,
                end_char=current_start + len(chunk_content),
                token_count=current_tokens,
                section_title=section_title,
            ))

        return chunks
