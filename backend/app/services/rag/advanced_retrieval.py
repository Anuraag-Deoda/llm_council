"""
Advanced retrieval service with confidence-based adaptive retrieval.

Replaces static top_k with:
- Confidence-based retrieval (stop when cumulative authority >= threshold)
- Query complexity analysis for adaptive retrieval
- Full explainability for each retrieved chunk
"""
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
import math

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
class ScoreExplanation:
    """Detailed explanation of why a chunk was retrieved and scored."""
    # Score components
    similarity_score: float
    similarity_contribution: float
    source_trust_score: float
    source_trust_contribution: float
    recency_score: float
    recency_contribution: float
    author_authority_score: float
    author_authority_contribution: float
    final_score: float

    # Ranking info
    rank: int
    cumulative_authority: float
    retrieval_reason: str

    # Comparison info
    beat_count: int
    was_better_because: List[str]

    # Weight info
    weights_used: Dict[str, float]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scores": {
                "similarity": {
                    "score": round(self.similarity_score, 4),
                    "contribution": round(self.similarity_contribution, 4),
                    "weight": round(self.weights_used.get("similarity", 0), 2)
                },
                "source_trust": {
                    "score": round(self.source_trust_score, 4),
                    "contribution": round(self.source_trust_contribution, 4),
                    "weight": round(self.weights_used.get("source_trust", 0), 2)
                },
                "recency": {
                    "score": round(self.recency_score, 4),
                    "contribution": round(self.recency_contribution, 4),
                    "weight": round(self.weights_used.get("recency", 0), 2)
                },
                "author_authority": {
                    "score": round(self.author_authority_score, 4),
                    "contribution": round(self.author_authority_contribution, 4),
                    "weight": round(self.weights_used.get("author_authority", 0), 2)
                }
            },
            "final_score": round(self.final_score, 4),
            "rank": self.rank,
            "cumulative_authority": round(self.cumulative_authority, 4),
            "retrieval_reason": self.retrieval_reason,
            "beat_count": self.beat_count,
            "was_better_because": self.was_better_because
        }


@dataclass
class ExplainedChunk:
    """A chunk with full explanation of why it was retrieved."""
    chunk_id: int
    document_id: int
    content: str
    source_name: str
    source_type: str
    document_title: str
    author: Optional[str]
    section_title: Optional[str]
    source_updated_at: Optional[datetime]
    explanation: ScoreExplanation
    extra_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AdaptiveRetrievalResult:
    """Result of an adaptive retrieval operation."""
    query: str
    chunks: List[ExplainedChunk]
    total_candidates: int
    chunks_retrieved: int
    retrieval_time_ms: int

    # Adaptive retrieval metadata
    authority_threshold: float
    authority_achieved: float
    stopped_reason: str  # "threshold_reached", "max_chunks", "no_more_candidates"
    query_complexity: str  # "simple", "moderate", "complex"

    # Cost savings
    chunks_saved: int  # How many chunks we didn't need to include

    log_id: Optional[int] = None


class QueryComplexityAnalyzer:
    """Analyzes query complexity to adjust retrieval parameters."""

    COMPLEXITY_INDICATORS = {
        "simple": {
            "max_words": 5,
            "question_words": ["what", "who", "when", "where"],
            "authority_threshold": 0.7,
            "max_chunks": 5
        },
        "moderate": {
            "max_words": 15,
            "question_words": ["how", "why", "explain"],
            "authority_threshold": 0.8,
            "max_chunks": 8
        },
        "complex": {
            "max_words": float("inf"),
            "question_words": ["compare", "analyze", "evaluate", "discuss"],
            "authority_threshold": 0.9,
            "max_chunks": 12
        }
    }

    def analyze(self, query: str) -> Tuple[str, float, int]:
        """
        Analyze query complexity.

        Returns:
            Tuple of (complexity_level, authority_threshold, max_chunks)
        """
        query_lower = query.lower()
        words = query_lower.split()
        word_count = len(words)

        # Check for complex indicators first
        for indicator in self.COMPLEXITY_INDICATORS["complex"]["question_words"]:
            if indicator in query_lower:
                config = self.COMPLEXITY_INDICATORS["complex"]
                return "complex", config["authority_threshold"], config["max_chunks"]

        # Check for moderate indicators
        for indicator in self.COMPLEXITY_INDICATORS["moderate"]["question_words"]:
            if indicator in query_lower:
                config = self.COMPLEXITY_INDICATORS["moderate"]
                return "moderate", config["authority_threshold"], config["max_chunks"]

        # Use word count for remaining classification
        if word_count <= self.COMPLEXITY_INDICATORS["simple"]["max_words"]:
            config = self.COMPLEXITY_INDICATORS["simple"]
            return "simple", config["authority_threshold"], config["max_chunks"]
        elif word_count <= self.COMPLEXITY_INDICATORS["moderate"]["max_words"]:
            config = self.COMPLEXITY_INDICATORS["moderate"]
            return "moderate", config["authority_threshold"], config["max_chunks"]
        else:
            config = self.COMPLEXITY_INDICATORS["complex"]
            return "complex", config["authority_threshold"], config["max_chunks"]


class AdvancedRetrievalService:
    """
    Advanced retrieval service with confidence-based adaptive retrieval.

    Key improvements over basic retrieval:
    1. Stops when cumulative authority reaches threshold (saves cost)
    2. Adapts retrieval based on query complexity
    3. Provides full explainability for each chunk
    4. Tracks why each chunk beat others
    """

    def __init__(
        self,
        embedding_service: EmbeddingService = None,
        trust_scorer: TrustScorer = None,
        base_authority_threshold: float = 0.8,
        absolute_max_chunks: int = 15,
        similarity_threshold: float = None,
    ):
        self.embedding_service = embedding_service or EmbeddingService()
        self.trust_scorer = trust_scorer or TrustScorer()
        self.base_authority_threshold = base_authority_threshold
        self.absolute_max_chunks = absolute_max_chunks
        self.similarity_threshold = similarity_threshold or settings.rag_similarity_threshold
        self.complexity_analyzer = QueryComplexityAnalyzer()

    async def retrieve(
        self,
        db: Session,
        query: str,
        authority_threshold: float = None,
        max_chunks: int = None,
        source_ids: List[int] = None,
        conversation_id: str = None,
        log_retrieval: bool = True,
    ) -> AdaptiveRetrievalResult:
        """
        Retrieve relevant chunks using adaptive confidence-based retrieval.

        Args:
            db: Database session
            query: Search query
            authority_threshold: Override cumulative authority threshold
            max_chunks: Override maximum chunks
            source_ids: Filter by specific source IDs
            conversation_id: Optional conversation ID for logging
            log_retrieval: Whether to log the retrieval

        Returns:
            AdaptiveRetrievalResult with explained chunks
        """
        start_time = time.time()

        # Analyze query complexity
        complexity, auto_threshold, auto_max = self.complexity_analyzer.analyze(query)

        # Use provided values or auto-determined values
        authority_threshold = authority_threshold or auto_threshold
        max_chunks = min(max_chunks or auto_max, self.absolute_max_chunks)

        # Generate query embedding
        query_embedding = await self.embedding_service.embed_query(query)

        # Fetch more candidates than we might need
        candidate_count = max_chunks * 3
        raw_results = self._vector_search(db, query_embedding, candidate_count, source_ids)

        # Filter by similarity threshold
        filtered_results = [
            r for r in raw_results
            if r['similarity'] >= self.similarity_threshold
        ]

        total_candidates = len(filtered_results)

        # Score all filtered results
        scored_chunks = []
        if filtered_results:
            for result in filtered_results:
                scored = self._score_chunk_with_explanation(result)
                scored_chunks.append(scored)

            # Sort by final score
            scored_chunks.sort(key=lambda x: x.explanation.final_score, reverse=True)

        # Adaptive retrieval: stop when cumulative authority >= threshold
        selected_chunks = []
        cumulative_authority = 0.0
        stopped_reason = "no_more_candidates"

        for i, chunk in enumerate(scored_chunks):
            if i >= max_chunks:
                stopped_reason = "max_chunks"
                break

            # Update rank and cumulative authority
            chunk.explanation.rank = i + 1
            cumulative_authority += chunk.explanation.final_score
            chunk.explanation.cumulative_authority = cumulative_authority

            # Determine retrieval reason
            if i == 0:
                chunk.explanation.retrieval_reason = "Highest relevance score"
            elif chunk.explanation.final_score > 0.8:
                chunk.explanation.retrieval_reason = "High confidence match"
            elif chunk.explanation.similarity_score > 0.85:
                chunk.explanation.retrieval_reason = "Strong semantic similarity"
            elif chunk.explanation.source_trust_score > 0.8:
                chunk.explanation.retrieval_reason = "Highly trusted source"
            else:
                chunk.explanation.retrieval_reason = "Additional context"

            # Track what this chunk beat
            chunk.explanation.beat_count = len(scored_chunks) - i - 1
            chunk.explanation.was_better_because = self._explain_ranking(
                chunk, scored_chunks[i+1] if i+1 < len(scored_chunks) else None
            )

            selected_chunks.append(chunk)

            # Check if we've reached authority threshold
            if cumulative_authority >= authority_threshold:
                stopped_reason = "threshold_reached"
                break

        retrieval_time_ms = int((time.time() - start_time) * 1000)

        # Log retrieval if requested
        log_id = None
        if log_retrieval:
            log_id = self._log_retrieval(
                db, query, query_embedding,
                selected_chunks, retrieval_time_ms,
                source_ids, conversation_id,
                authority_threshold, cumulative_authority
            )

        return AdaptiveRetrievalResult(
            query=query,
            chunks=selected_chunks,
            total_candidates=total_candidates,
            chunks_retrieved=len(selected_chunks),
            retrieval_time_ms=retrieval_time_ms,
            authority_threshold=authority_threshold,
            authority_achieved=cumulative_authority,
            stopped_reason=stopped_reason,
            query_complexity=complexity,
            chunks_saved=total_candidates - len(selected_chunks),
            log_id=log_id,
        )

    def _score_chunk_with_explanation(
        self,
        chunk: Dict[str, Any]
    ) -> ExplainedChunk:
        """Score a chunk and create full explanation."""
        # Get weights
        weights = {
            "similarity": self.trust_scorer.weight_similarity,
            "source_trust": self.trust_scorer.weight_source_trust,
            "recency": self.trust_scorer.weight_recency,
            "author_authority": self.trust_scorer.weight_author_authority,
        }

        # Get individual scores
        similarity_score = chunk.get('similarity', 0)

        source_type = chunk.get('source_type', 'document').lower()
        source_trust = chunk.get('source_base_trust_score') or self.trust_scorer._get_source_trust(source_type)

        recency_score = self.trust_scorer._compute_recency_score(chunk.get('source_updated_at'))

        author_trust = chunk.get('author_trust_score', 0.5)

        # Calculate contributions
        similarity_contribution = weights["similarity"] * similarity_score
        source_trust_contribution = weights["source_trust"] * source_trust
        recency_contribution = weights["recency"] * recency_score
        author_authority_contribution = weights["author_authority"] * author_trust

        final_score = (
            similarity_contribution +
            source_trust_contribution +
            recency_contribution +
            author_authority_contribution
        )

        explanation = ScoreExplanation(
            similarity_score=similarity_score,
            similarity_contribution=similarity_contribution,
            source_trust_score=source_trust,
            source_trust_contribution=source_trust_contribution,
            recency_score=recency_score,
            recency_contribution=recency_contribution,
            author_authority_score=author_trust,
            author_authority_contribution=author_authority_contribution,
            final_score=final_score,
            rank=0,  # Will be set later
            cumulative_authority=0,  # Will be set later
            retrieval_reason="",  # Will be set later
            beat_count=0,  # Will be set later
            was_better_because=[],  # Will be set later
            weights_used=weights,
        )

        return ExplainedChunk(
            chunk_id=chunk.get('chunk_id'),
            document_id=chunk.get('document_id'),
            content=chunk.get('content', ''),
            source_name=chunk.get('source_name', 'unknown'),
            source_type=source_type,
            document_title=chunk.get('document_title', 'Untitled'),
            author=chunk.get('author'),
            section_title=chunk.get('section_title'),
            source_updated_at=chunk.get('source_updated_at'),
            explanation=explanation,
            extra_data=chunk.get('extra_data', {}),
        )

    def _explain_ranking(
        self,
        current: ExplainedChunk,
        next_chunk: Optional[ExplainedChunk]
    ) -> List[str]:
        """Explain why current chunk ranked higher than next."""
        if not next_chunk:
            return ["Highest overall score"]

        reasons = []
        exp = current.explanation
        next_exp = next_chunk.explanation

        # Check which component made the difference
        sim_diff = exp.similarity_contribution - next_exp.similarity_contribution
        trust_diff = exp.source_trust_contribution - next_exp.source_trust_contribution
        recency_diff = exp.recency_contribution - next_exp.recency_contribution
        author_diff = exp.author_authority_contribution - next_exp.author_authority_contribution

        if sim_diff > 0.05:
            reasons.append(f"Higher semantic similarity (+{sim_diff:.2f})")
        if trust_diff > 0.03:
            reasons.append(f"More trusted source (+{trust_diff:.2f})")
        if recency_diff > 0.02:
            reasons.append(f"More recent content (+{recency_diff:.2f})")
        if author_diff > 0.02:
            reasons.append(f"Higher author authority (+{author_diff:.2f})")

        if not reasons:
            score_diff = exp.final_score - next_exp.final_score
            reasons.append(f"Marginally higher combined score (+{score_diff:.3f})")

        return reasons

    def _vector_search(
        self,
        db: Session,
        query_embedding: List[float],
        limit: int,
        source_ids: List[int] = None,
    ) -> List[Dict[str, Any]]:
        """Perform vector similarity search using pgvector."""
        embedding_str = f"[{','.join(str(x) for x in query_embedding)}]"

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

        params = {"embedding": embedding_str, "limit": limit}
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
        chunks: List[ExplainedChunk],
        retrieval_time_ms: int,
        source_filter: List[int] = None,
        conversation_id: str = None,
        authority_threshold: float = None,
        authority_achieved: float = None,
    ) -> int:
        """Log retrieval operation to database."""
        log = RetrievalLog(
            query=query,
            query_embedding=query_embedding,
            conversation_id=conversation_id,
            top_k=len(chunks),
            similarity_threshold=self.similarity_threshold,
            source_filter=source_filter or [],
            chunks_retrieved=len(chunks),
            chunk_ids=[c.chunk_id for c in chunks],
            similarity_scores=[c.explanation.similarity_score for c in chunks],
            trust_scores=[c.explanation.final_score for c in chunks],
            conflicts_detected=0,
            conflict_ids=[],
            retrieval_latency_ms=retrieval_time_ms,
            total_latency_ms=retrieval_time_ms,
            extra_data={
                "authority_threshold": authority_threshold,
                "authority_achieved": authority_achieved,
                "adaptive_retrieval": True,
            }
        )
        db.add(log)
        db.commit()
        return log.id

    def build_context_with_explanations(
        self,
        chunks: List[ExplainedChunk],
        include_explanations: bool = False,
        max_tokens: int = None,
    ) -> Tuple[str, List[Dict]]:
        """
        Build context string from retrieved chunks.

        Returns:
            Tuple of (context_string, explanations_list)
        """
        if not chunks:
            return "", []

        context_parts = []
        explanations = []
        total_tokens = 0

        for chunk in chunks:
            header = f"[Source {chunk.explanation.rank}: {chunk.source_name} - {chunk.document_title}"
            if chunk.section_title:
                header += f" - {chunk.section_title}"
            header += f" (relevance: {chunk.explanation.final_score:.0%})]"

            part = f"{header}\n{chunk.content}\n"

            # Rough token estimate
            part_tokens = len(part) // 4

            if max_tokens and total_tokens + part_tokens > max_tokens:
                break

            context_parts.append(part)
            total_tokens += part_tokens

            if include_explanations:
                explanations.append({
                    "chunk_id": chunk.chunk_id,
                    "rank": chunk.explanation.rank,
                    "document_title": chunk.document_title,
                    "source_name": chunk.source_name,
                    "explanation": chunk.explanation.to_dict()
                })

        return "\n".join(context_parts), explanations
