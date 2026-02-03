"""
Retrieval service for RAG vector search and chunk retrieval.
"""
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
import time

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.database.rag_models import (
    DocumentChunk, Document, DocumentSource, RetrievalLog
)
from .embedding_service import EmbeddingService
from .trust_scorer import TrustScorer, ScoredChunk

logger = logging.getLogger(__name__)


@dataclass
class RetrievalResult:
    """Result of a retrieval operation."""
    query: str
    chunks: List[ScoredChunk]
    total_retrieved: int
    retrieval_time_ms: int
    log_id: Optional[int] = None


class RetrievalService:
    """
    Service for retrieving relevant document chunks using vector similarity search.

    Uses pgvector for efficient approximate nearest neighbor search
    and applies trust-based scoring to retrieved results.
    """

    def __init__(
        self,
        embedding_service: EmbeddingService = None,
        trust_scorer: TrustScorer = None,
        top_k: int = None,
        similarity_threshold: float = None,
    ):
        """
        Initialize the retrieval service.

        Args:
            embedding_service: Service for generating query embeddings
            trust_scorer: Service for scoring retrieved chunks
            top_k: Number of chunks to retrieve
            similarity_threshold: Minimum similarity score
        """
        self.embedding_service = embedding_service or EmbeddingService()
        self.trust_scorer = trust_scorer or TrustScorer()
        self.top_k = top_k or settings.rag_top_k
        self.similarity_threshold = similarity_threshold or settings.rag_similarity_threshold

    async def retrieve(
        self,
        db: Session,
        query: str,
        top_k: int = None,
        source_ids: List[int] = None,
        conversation_id: str = None,
        log_retrieval: bool = True,
    ) -> RetrievalResult:
        """
        Retrieve relevant chunks for a query.

        Args:
            db: Database session
            query: Search query
            top_k: Override default number of chunks to retrieve
            source_ids: Filter by specific source IDs
            conversation_id: Optional conversation ID for logging
            log_retrieval: Whether to log the retrieval

        Returns:
            RetrievalResult with scored chunks
        """
        start_time = time.time()
        top_k = top_k or self.top_k

        # Generate query embedding
        query_embedding = await self.embedding_service.embed_query(query)

        # Search for similar chunks
        raw_results = self._vector_search(
            db, query_embedding, top_k * 2, source_ids  # Fetch extra for filtering
        )

        # Filter by similarity threshold
        filtered_results = [
            r for r in raw_results
            if r['similarity'] >= self.similarity_threshold
        ][:top_k]

        # Score chunks with trust weights
        if filtered_results:
            chunks_for_scoring = []
            similarity_scores = []

            for result in filtered_results:
                chunks_for_scoring.append(result)
                similarity_scores.append(result['similarity'])

            scored_chunks = self.trust_scorer.score_chunks(
                chunks_for_scoring, similarity_scores
            )
        else:
            scored_chunks = []

        retrieval_time_ms = int((time.time() - start_time) * 1000)

        # Log retrieval if requested
        log_id = None
        if log_retrieval:
            log_id = self._log_retrieval(
                db, query, query_embedding,
                scored_chunks, retrieval_time_ms,
                source_ids, conversation_id
            )

        return RetrievalResult(
            query=query,
            chunks=scored_chunks,
            total_retrieved=len(scored_chunks),
            retrieval_time_ms=retrieval_time_ms,
            log_id=log_id,
        )

    def _vector_search(
        self,
        db: Session,
        query_embedding: List[float],
        limit: int,
        source_ids: List[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Perform vector similarity search using pgvector.

        Args:
            db: Database session
            query_embedding: Query embedding vector
            limit: Maximum results
            source_ids: Optional filter by source IDs

        Returns:
            List of chunk dicts with similarity scores
        """
        # Build the query using pgvector's <=> operator (cosine distance)
        # Cosine similarity = 1 - cosine distance
        embedding_str = f"[{','.join(str(x) for x in query_embedding)}]"

        # Build SQL query with optional source filter
        base_query = """
            SELECT
                c.id as chunk_id,
                c.document_id,
                c.content,
                c.chunk_index,
                c.token_count,
                c.section_title,
                c.extra_data as chunk_extra_data,
                1 - (c.embedding <=> :embedding::vector) as similarity,
                d.title as document_title,
                d.author,
                d.author_trust_score,
                d.source_updated_at,
                d.extra_data as doc_extra_data,
                s.id as source_id,
                s.name as source_name,
                s.source_type,
                s.base_trust_score as source_base_trust_score
            FROM rag_document_chunks c
            JOIN rag_documents d ON c.document_id = d.id
            JOIN rag_document_sources s ON d.source_id = s.id
            WHERE c.embedding IS NOT NULL
              AND d.status = 'completed'
              AND s.is_active = true
        """

        if source_ids:
            base_query += " AND s.id = ANY(:source_ids)"

        base_query += """
            ORDER BY c.embedding <=> :embedding::vector
            LIMIT :limit
        """

        params = {
            "embedding": embedding_str,
            "limit": limit,
        }
        if source_ids:
            params["source_ids"] = source_ids

        result = db.execute(text(base_query), params)

        chunks = []
        for row in result:
            chunks.append({
                "chunk_id": row.chunk_id,
                "document_id": row.document_id,
                "content": row.content,
                "chunk_index": row.chunk_index,
                "token_count": row.token_count,
                "section_title": row.section_title,
                "extra_data": row.chunk_extra_data or {},
                "similarity": float(row.similarity),
                "document_title": row.document_title,
                "author": row.author,
                "author_trust_score": row.author_trust_score,
                "source_updated_at": row.source_updated_at,
                "doc_extra_data": row.doc_extra_data or {},
                "source_id": row.source_id,
                "source_name": row.source_name,
                "source_type": row.source_type.value if hasattr(row.source_type, 'value') else row.source_type,
                "source_base_trust_score": row.source_base_trust_score,
            })

        return chunks

    def _log_retrieval(
        self,
        db: Session,
        query: str,
        query_embedding: List[float],
        chunks: List[ScoredChunk],
        retrieval_time_ms: int,
        source_filter: List[int] = None,
        conversation_id: str = None,
    ) -> int:
        """
        Log retrieval operation to database.

        Args:
            db: Database session
            query: Original query
            query_embedding: Query embedding
            chunks: Retrieved and scored chunks
            retrieval_time_ms: Time taken for retrieval
            source_filter: Source IDs that were filtered
            conversation_id: Optional conversation ID

        Returns:
            ID of the created log entry
        """
        log = RetrievalLog(
            query=query,
            query_embedding=query_embedding,
            conversation_id=conversation_id,
            top_k=self.top_k,
            similarity_threshold=self.similarity_threshold,
            source_filter=source_filter or [],
            chunks_retrieved=len(chunks),
            chunk_ids=[c.chunk_id for c in chunks],
            similarity_scores=[c.similarity_score for c in chunks],
            trust_scores=[c.final_score for c in chunks],
            conflicts_detected=0,  # Will be updated by conflict detector
            conflict_ids=[],
            retrieval_latency_ms=retrieval_time_ms,
            total_latency_ms=retrieval_time_ms,  # Will be updated later
        )
        db.add(log)
        db.commit()
        return log.id

    async def get_chunk_by_id(
        self,
        db: Session,
        chunk_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Get a specific chunk by ID with full metadata.

        Args:
            db: Database session
            chunk_id: Chunk ID

        Returns:
            Chunk dict or None if not found
        """
        result = db.execute(
            text("""
                SELECT
                    c.id as chunk_id,
                    c.document_id,
                    c.content,
                    c.chunk_index,
                    c.token_count,
                    c.section_title,
                    c.extra_data as chunk_extra_data,
                    d.title as document_title,
                    d.author,
                    d.author_trust_score,
                    d.source_updated_at,
                    s.name as source_name,
                    s.source_type
                FROM rag_document_chunks c
                JOIN rag_documents d ON c.document_id = d.id
                JOIN rag_document_sources s ON d.source_id = s.id
                WHERE c.id = :chunk_id
            """),
            {"chunk_id": chunk_id}
        ).first()

        if not result:
            return None

        return {
            "chunk_id": result.chunk_id,
            "document_id": result.document_id,
            "content": result.content,
            "chunk_index": result.chunk_index,
            "token_count": result.token_count,
            "section_title": result.section_title,
            "extra_data": result.chunk_extra_data or {},
            "document_title": result.document_title,
            "author": result.author,
            "author_trust_score": result.author_trust_score,
            "source_updated_at": result.source_updated_at,
            "source_name": result.source_name,
            "source_type": result.source_type.value if hasattr(result.source_type, 'value') else result.source_type,
        }

    def build_context(
        self,
        chunks: List[ScoredChunk],
        include_metadata: bool = True,
        max_tokens: int = None,
    ) -> str:
        """
        Build a context string from retrieved chunks.

        Args:
            chunks: List of scored chunks
            include_metadata: Whether to include source metadata
            max_tokens: Maximum tokens for context

        Returns:
            Formatted context string
        """
        if not chunks:
            return ""

        context_parts = []
        total_tokens = 0

        for i, chunk in enumerate(chunks, 1):
            if include_metadata:
                header = f"[Source {i}: {chunk.source_name} - {chunk.document_title}"
                if chunk.section_title:
                    header += f" - {chunk.section_title}"
                header += f" (confidence: {chunk.final_score:.2f})]"

                part = f"{header}\n{chunk.content}\n"
            else:
                part = f"[{i}] {chunk.content}\n"

            # Rough token estimate (4 chars per token)
            part_tokens = len(part) // 4

            if max_tokens and total_tokens + part_tokens > max_tokens:
                break

            context_parts.append(part)
            total_tokens += part_tokens

        return "\n".join(context_parts)
