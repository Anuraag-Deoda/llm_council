"""
RAG Orchestrator - Main coordination service for retrieval-augmented generation.

Coordinates document retrieval, trust scoring, and conflict detection
to build augmented prompts for the council.
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
import time

from sqlalchemy.orm import Session

from app.config import settings
from app.database.rag_models import RetrievalLog
from .embedding_service import EmbeddingService
from .retrieval_service import RetrievalService, RetrievalResult
from .trust_scorer import TrustScorer, ScoredChunk
from .conflict_detector import ConflictDetector, DetectedConflict

logger = logging.getLogger(__name__)


@dataclass
class RAGContext:
    """Complete RAG context for a query."""
    query: str
    chunks: List[ScoredChunk]
    conflicts: List[DetectedConflict]
    context_text: str
    conflict_warning: str
    retrieval_time_ms: int
    conflict_detection_time_ms: int
    total_time_ms: int
    retrieval_log_id: Optional[int] = None
    extra_data: Dict[str, Any] = field(default_factory=dict)


class RAGOrchestrator:
    """
    Main orchestrator for RAG operations.

    Coordinates:
    1. Query embedding and vector search
    2. Trust-based scoring of retrieved chunks
    3. Conflict detection between sources
    4. Context building for LLM prompts
    """

    def __init__(
        self,
        embedding_service: EmbeddingService = None,
        retrieval_service: RetrievalService = None,
        trust_scorer: TrustScorer = None,
        conflict_detector: ConflictDetector = None,
    ):
        """
        Initialize the RAG orchestrator.

        Args:
            embedding_service: Service for generating embeddings
            retrieval_service: Service for vector search
            trust_scorer: Service for scoring chunks
            conflict_detector: Service for detecting conflicts
        """
        self.embedding_service = embedding_service or EmbeddingService()
        self.trust_scorer = trust_scorer or TrustScorer()
        self.conflict_detector = conflict_detector or ConflictDetector()
        self.retrieval_service = retrieval_service or RetrievalService(
            embedding_service=self.embedding_service,
            trust_scorer=self.trust_scorer,
        )

    async def get_context(
        self,
        db: Session,
        query: str,
        top_k: int = None,
        source_ids: List[int] = None,
        detect_conflicts: bool = True,
        conversation_id: str = None,
        max_context_tokens: int = 2000,
    ) -> RAGContext:
        """
        Get full RAG context for a query.

        Args:
            db: Database session
            query: User query
            top_k: Number of chunks to retrieve
            source_ids: Filter by specific source IDs
            detect_conflicts: Whether to run conflict detection
            conversation_id: Optional conversation ID for logging
            max_context_tokens: Maximum tokens for context

        Returns:
            RAGContext with all retrieval results
        """
        start_time = time.time()

        # Step 1: Retrieve relevant chunks
        retrieval_result = await self.retrieval_service.retrieve(
            db=db,
            query=query,
            top_k=top_k,
            source_ids=source_ids,
            conversation_id=conversation_id,
            log_retrieval=True,
        )

        retrieval_time_ms = retrieval_result.retrieval_time_ms

        # Step 2: Detect conflicts (if enabled and enough chunks)
        conflicts = []
        conflict_detection_time_ms = 0

        if detect_conflicts and len(retrieval_result.chunks) >= 2:
            conflict_start = time.time()
            try:
                conflicts = await self.conflict_detector.detect_conflicts(
                    retrieval_result.chunks
                )

                # Save conflicts to database
                if conflicts:
                    conflict_ids = self.conflict_detector.save_conflicts(
                        db=db,
                        conflicts=conflicts,
                        query=query,
                        retrieval_log_id=retrieval_result.log_id,
                    )

                    # Update retrieval log with conflict info
                    if retrieval_result.log_id:
                        log = db.query(RetrievalLog).get(retrieval_result.log_id)
                        if log:
                            log.conflicts_detected = len(conflicts)
                            log.conflict_ids = conflict_ids
                            db.commit()

            except Exception as e:
                logger.error(f"Conflict detection failed: {e}")

            conflict_detection_time_ms = int((time.time() - conflict_start) * 1000)

        # Step 3: Build context text
        context_text = self.retrieval_service.build_context(
            retrieval_result.chunks,
            include_metadata=True,
            max_tokens=max_context_tokens,
        )

        # Step 4: Build conflict warning
        conflict_warning = ""
        if conflicts:
            conflict_warning = self.conflict_detector.format_conflict_for_prompt(conflicts)

        total_time_ms = int((time.time() - start_time) * 1000)

        # Update retrieval log with total time
        if retrieval_result.log_id:
            log = db.query(RetrievalLog).get(retrieval_result.log_id)
            if log:
                log.total_latency_ms = total_time_ms
                db.commit()

        return RAGContext(
            query=query,
            chunks=retrieval_result.chunks,
            conflicts=conflicts,
            context_text=context_text,
            conflict_warning=conflict_warning,
            retrieval_time_ms=retrieval_time_ms,
            conflict_detection_time_ms=conflict_detection_time_ms,
            total_time_ms=total_time_ms,
            retrieval_log_id=retrieval_result.log_id,
        )

    def build_augmented_prompt(
        self,
        original_prompt: str,
        rag_context: RAGContext,
        include_sources: bool = True,
    ) -> str:
        """
        Build an augmented prompt with RAG context.

        Args:
            original_prompt: Original user prompt
            rag_context: RAG context from get_context()
            include_sources: Whether to include source citations

        Returns:
            Augmented prompt string
        """
        parts = []

        # Add context preamble if we have chunks
        if rag_context.chunks:
            parts.append(
                "The following relevant information has been retrieved from the knowledge base. "
                "Use this context to inform your response, but also apply your own knowledge and reasoning.\n"
            )

            # Add context
            parts.append("### Retrieved Context ###")
            parts.append(rag_context.context_text)
            parts.append("### End of Context ###\n")

        # Add conflict warning if present
        if rag_context.conflict_warning:
            parts.append(rag_context.conflict_warning)

        # Add original prompt
        parts.append("### User Query ###")
        parts.append(original_prompt)

        # Add instructions for source citation
        if include_sources and rag_context.chunks:
            parts.append(
                "\nWhen using information from the retrieved context, "
                "please cite the source (e.g., 'According to [Source Name]...')."
            )

        return "\n".join(parts)

    def format_stream_chunk(
        self,
        chunk_type: str,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Format a streaming chunk for the frontend.

        Args:
            chunk_type: Type of chunk (rag_context, conflict_detected)
            data: Chunk data

        Returns:
            Formatted chunk dict
        """
        return {
            "type": chunk_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
        }

    def get_context_stream_chunk(self, rag_context: RAGContext) -> Dict[str, Any]:
        """
        Create a stream chunk for RAG context information.

        Args:
            rag_context: The RAG context

        Returns:
            Stream chunk dict
        """
        return self.format_stream_chunk("rag_context", {
            "chunks_retrieved": len(rag_context.chunks),
            "sources": list(set(c.source_name for c in rag_context.chunks)),
            "documents": list(set(c.document_title for c in rag_context.chunks)),
            "retrieval_time_ms": rag_context.retrieval_time_ms,
            "top_chunks": [
                {
                    "document_title": c.document_title,
                    "source_name": c.source_name,
                    "section_title": c.section_title,
                    "score": c.final_score,
                    "similarity": c.similarity_score,
                }
                for c in rag_context.chunks[:5]
            ],
        })

    def get_conflict_stream_chunk(self, conflicts: List[DetectedConflict]) -> Dict[str, Any]:
        """
        Create a stream chunk for detected conflicts.

        Args:
            conflicts: List of detected conflicts

        Returns:
            Stream chunk dict
        """
        return self.format_stream_chunk("conflict_detected", {
            "conflicts": [
                {
                    "type": c.conflict_type.value,
                    "confidence": c.confidence,
                    "source_a": {
                        "name": c.chunk_a_source,
                        "author": c.chunk_a_author,
                        "content_preview": c.chunk_a_content[:200],
                    },
                    "source_b": {
                        "name": c.chunk_b_source,
                        "author": c.chunk_b_author,
                        "content_preview": c.chunk_b_content[:200],
                    },
                    "explanation": c.explanation,
                    "recommendation": c.recommendation,
                }
                for c in conflicts
            ],
        })

    async def query(
        self,
        db: Session,
        query: str,
        top_k: int = None,
        source_ids: List[int] = None,
        include_conflict_detection: bool = True,
    ) -> Dict[str, Any]:
        """
        Execute a direct RAG query (without council integration).

        Args:
            db: Database session
            query: User query
            top_k: Number of chunks to retrieve
            source_ids: Filter by source IDs
            include_conflict_detection: Whether to detect conflicts

        Returns:
            Query result dict with context and conflicts
        """
        rag_context = await self.get_context(
            db=db,
            query=query,
            top_k=top_k,
            source_ids=source_ids,
            detect_conflicts=include_conflict_detection,
        )

        return {
            "query": query,
            "context": rag_context.context_text,
            "chunks": [
                {
                    "chunk_id": c.chunk_id,
                    "document_id": c.document_id,
                    "document_title": c.document_title,
                    "source_name": c.source_name,
                    "source_type": c.source_type,
                    "content": c.content,
                    "section_title": c.section_title,
                    "scores": {
                        "final": c.final_score,
                        "similarity": c.similarity_score,
                        "source_trust": c.source_trust_score,
                        "recency": c.recency_score,
                        "author_authority": c.author_authority_score,
                    },
                }
                for c in rag_context.chunks
            ],
            "conflicts": [
                {
                    "type": c.conflict_type.value,
                    "confidence": c.confidence,
                    "source_a": c.chunk_a_source,
                    "source_b": c.chunk_b_source,
                    "explanation": c.explanation,
                    "recommendation": c.recommendation,
                }
                for c in rag_context.conflicts
            ],
            "conflict_report": self.conflict_detector.format_conflict_report(rag_context.conflicts),
            "timing": {
                "retrieval_ms": rag_context.retrieval_time_ms,
                "conflict_detection_ms": rag_context.conflict_detection_time_ms,
                "total_ms": rag_context.total_time_ms,
            },
        }
