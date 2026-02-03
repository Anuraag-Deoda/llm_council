"""
Document ingestion services for various sources.
"""
from .base_ingestor import BaseIngestor
from .document_ingestor import DocumentIngestor

__all__ = [
    "BaseIngestor",
    "DocumentIngestor",
]
