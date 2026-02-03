"""
RAG (Retrieval-Augmented Generation) database models for LLM Council.

This module defines models for document storage, chunking, embeddings,
conflict detection, and retrieval logging.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Float, Boolean,
    JSON, ForeignKey, Index, Enum as SQLEnum, LargeBinary
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
import enum

from .models import Base


class SourceType(str, enum.Enum):
    """Document source type enumeration"""
    DOCUMENT = "document"  # Uploaded files (PDF, DOCX, TXT, MD)
    SLACK = "slack"
    NOTION = "notion"
    GITHUB = "github"
    WEB = "web"


class DocumentStatus(str, enum.Enum):
    """Document processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ConflictType(str, enum.Enum):
    """Types of detected conflicts between sources"""
    FACTUAL = "factual"  # Contradictory facts
    TEMPORAL = "temporal"  # Outdated vs newer information
    OPINION = "opinion"  # Differing opinions/interpretations
    NUMERICAL = "numerical"  # Conflicting numbers/statistics
    PROCEDURAL = "procedural"  # Different processes/steps


class ConflictStatus(str, enum.Enum):
    """Conflict resolution status"""
    DETECTED = "detected"
    REVIEWED = "reviewed"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class DocumentSource(Base):
    """
    Configuration for document sources (e.g., Slack workspace, Notion database).
    """
    __tablename__ = "rag_document_sources"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    source_type = Column(SQLEnum(SourceType), nullable=False, index=True)
    description = Column(Text, nullable=True)

    # Trust configuration
    base_trust_score = Column(Float, default=0.7, nullable=False)

    # Connection configuration (encrypted in practice)
    connection_config = Column(JSON, default=dict)  # API keys, URLs, etc.
    sync_config = Column(JSON, default=dict)  # Sync frequency, filters, etc.

    # Status
    is_active = Column(Boolean, default=True, index=True)
    last_sync_at = Column(DateTime(timezone=True), nullable=True)
    last_sync_status = Column(String(50), nullable=True)
    last_sync_error = Column(Text, nullable=True)
    document_count = Column(Integer, default=0)

    # Metadata
    extra_data = Column(JSON, default=dict)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    # Relationships
    documents = relationship("Document", back_populates="source", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_source_type_active', 'source_type', 'is_active'),
    )


class Document(Base):
    """
    Ingested documents from various sources.
    """
    __tablename__ = "rag_documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_id = Column(Integer, ForeignKey("rag_document_sources.id", ondelete="CASCADE"), nullable=False, index=True)

    # Document identification
    external_id = Column(String(255), nullable=True, index=True)  # ID in source system
    title = Column(String(500), nullable=False)
    file_path = Column(String(1000), nullable=True)  # For uploaded files
    file_type = Column(String(50), nullable=True)  # pdf, docx, txt, md, etc.
    url = Column(String(2000), nullable=True)  # Original URL if applicable

    # Content
    content = Column(Text, nullable=True)  # Full text content
    content_hash = Column(String(64), nullable=False, index=True)  # SHA256 for deduplication

    # Trust and authority
    author = Column(String(255), nullable=True)
    author_trust_score = Column(Float, default=0.5)  # 0.0 - 1.0

    # Processing status
    status = Column(SQLEnum(DocumentStatus), default=DocumentStatus.PENDING, nullable=False, index=True)
    error_message = Column(Text, nullable=True)
    chunk_count = Column(Integer, default=0)
    token_count = Column(Integer, default=0)

    # Metadata
    extra_data = Column(JSON, default=dict)  # Source-specific metadata
    tags = Column(JSON, default=list)  # User-defined tags

    # Timestamps
    source_created_at = Column(DateTime(timezone=True), nullable=True)  # When created in source
    source_updated_at = Column(DateTime(timezone=True), nullable=True)  # When updated in source
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    indexed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    source = relationship("DocumentSource", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_doc_source_status', 'source_id', 'status'),
        Index('idx_doc_hash', 'content_hash'),
        Index('idx_doc_created', 'created_at'),
    )


class DocumentChunk(Base):
    """
    Document chunks with vector embeddings for similarity search.
    """
    __tablename__ = "rag_document_chunks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("rag_documents.id", ondelete="CASCADE"), nullable=False, index=True)

    # Chunk content
    content = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)  # Order within document
    start_char = Column(Integer, nullable=True)  # Start position in original doc
    end_char = Column(Integer, nullable=True)  # End position in original doc
    token_count = Column(Integer, nullable=False)

    # Vector embedding (1536 dimensions for text-embedding-3-small)
    embedding = Column(Vector(1536), nullable=True)
    embedding_model = Column(String(100), nullable=True)

    # Metadata for context
    section_title = Column(String(500), nullable=True)  # Header/section this belongs to
    extra_data = Column(JSON, default=dict)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    # Relationships
    document = relationship("Document", back_populates="chunks")
    conflicts_as_a = relationship("ConflictRecord", foreign_keys="ConflictRecord.chunk_a_id", back_populates="chunk_a", cascade="all, delete-orphan")
    conflicts_as_b = relationship("ConflictRecord", foreign_keys="ConflictRecord.chunk_b_id", back_populates="chunk_b", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_chunk_doc_index', 'document_id', 'chunk_index'),
    )


class ConflictRecord(Base):
    """
    Records of detected conflicts between document chunks.
    """
    __tablename__ = "rag_conflict_records"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Conflicting chunks
    chunk_a_id = Column(Integer, ForeignKey("rag_document_chunks.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_b_id = Column(Integer, ForeignKey("rag_document_chunks.id", ondelete="CASCADE"), nullable=False, index=True)

    # Conflict details
    conflict_type = Column(SQLEnum(ConflictType), nullable=False, index=True)
    confidence = Column(Float, nullable=False)  # 0.0 - 1.0
    explanation = Column(Text, nullable=True)  # LLM explanation of the conflict
    recommendation = Column(Text, nullable=True)  # Suggested resolution

    # Status and resolution
    status = Column(SQLEnum(ConflictStatus), default=ConflictStatus.DETECTED, nullable=False, index=True)
    resolved_by = Column(String(255), nullable=True)  # User who resolved
    resolution_notes = Column(Text, nullable=True)
    preferred_chunk_id = Column(Integer, nullable=True)  # Which chunk is preferred after resolution

    # Detection context
    query = Column(Text, nullable=True)  # Query that triggered detection
    retrieval_log_id = Column(Integer, ForeignKey("rag_retrieval_logs.id", ondelete="SET NULL"), nullable=True)

    # Metadata
    extra_data = Column(JSON, default=dict)

    # Timestamps
    detected_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    chunk_a = relationship("DocumentChunk", foreign_keys=[chunk_a_id], back_populates="conflicts_as_a")
    chunk_b = relationship("DocumentChunk", foreign_keys=[chunk_b_id], back_populates="conflicts_as_b")

    __table_args__ = (
        Index('idx_conflict_chunks', 'chunk_a_id', 'chunk_b_id'),
        Index('idx_conflict_status_type', 'status', 'conflict_type'),
        Index('idx_conflict_confidence', 'confidence'),
    )


class RetrievalLog(Base):
    """
    Logs of RAG retrieval operations for analytics and debugging.
    """
    __tablename__ = "rag_retrieval_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Query details
    query = Column(Text, nullable=False)
    query_embedding = Column(Vector(1536), nullable=True)
    conversation_id = Column(String(100), nullable=True, index=True)

    # Retrieval parameters
    top_k = Column(Integer, nullable=False)
    similarity_threshold = Column(Float, nullable=True)
    source_filter = Column(JSON, default=list)  # Filter by source IDs

    # Results
    chunks_retrieved = Column(Integer, nullable=False)
    chunk_ids = Column(JSON, default=list)  # IDs of retrieved chunks
    similarity_scores = Column(JSON, default=list)  # Corresponding scores
    trust_scores = Column(JSON, default=list)  # Final weighted scores

    # Conflict detection
    conflicts_detected = Column(Integer, default=0)
    conflict_ids = Column(JSON, default=list)

    # Performance
    retrieval_latency_ms = Column(Integer, nullable=True)
    total_latency_ms = Column(Integer, nullable=True)

    # Metadata
    extra_data = Column(JSON, default=dict)

    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    __table_args__ = (
        Index('idx_retrieval_conv', 'conversation_id', 'created_at'),
        Index('idx_retrieval_created', 'created_at'),
    )
