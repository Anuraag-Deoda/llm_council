"""
Abstract base class for document ingestors.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any
import hashlib


@dataclass
class IngestedDocument:
    """Represents a document ready for processing."""
    title: str
    content: str
    content_hash: str
    file_type: Optional[str] = None
    file_path: Optional[str] = None
    url: Optional[str] = None
    external_id: Optional[str] = None
    author: Optional[str] = None
    author_trust_score: float = 0.5
    source_created_at: Optional[datetime] = None
    source_updated_at: Optional[datetime] = None
    extra_data: Dict[str, Any] = None

    def __post_init__(self):
        if self.extra_data is None:
            self.extra_data = {}


class BaseIngestor(ABC):
    """
    Abstract base class for document ingestors.

    Subclasses implement extraction logic for specific source types
    (files, Slack, Notion, GitHub, etc.).
    """

    def __init__(self, source_name: str, base_trust_score: float = 0.7):
        """
        Initialize the ingestor.

        Args:
            source_name: Name of the document source
            base_trust_score: Default trust score for documents from this source
        """
        self.source_name = source_name
        self.base_trust_score = base_trust_score

    @abstractmethod
    async def extract_content(self, source_path: str, **kwargs) -> IngestedDocument:
        """
        Extract content from a source.

        Args:
            source_path: Path, URL, or identifier of the source
            **kwargs: Additional source-specific parameters

        Returns:
            IngestedDocument with extracted content
        """
        pass

    @abstractmethod
    async def extract_batch(
        self, source_paths: List[str], **kwargs
    ) -> List[IngestedDocument]:
        """
        Extract content from multiple sources.

        Args:
            source_paths: List of paths, URLs, or identifiers
            **kwargs: Additional source-specific parameters

        Returns:
            List of IngestedDocuments
        """
        pass

    @abstractmethod
    def get_supported_types(self) -> List[str]:
        """
        Get list of supported file types or source types.

        Returns:
            List of supported type identifiers
        """
        pass

    @staticmethod
    def compute_content_hash(content: str) -> str:
        """
        Compute SHA-256 hash of content for deduplication.

        Args:
            content: Document content

        Returns:
            Hex string of SHA-256 hash
        """
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def _extract_title_from_content(self, content: str, max_length: int = 100) -> str:
        """
        Extract a title from content if none provided.

        Args:
            content: Document content
            max_length: Maximum title length

        Returns:
            Extracted title
        """
        # Try to find a heading
        lines = content.strip().split('\n')
        for line in lines[:5]:  # Check first 5 lines
            line = line.strip()
            if line:
                # Check for markdown heading
                if line.startswith('#'):
                    return line.lstrip('#').strip()[:max_length]
                # Use first non-empty line
                return line[:max_length]
        return "Untitled Document"
