"""
Trust scoring service for RAG retrieved chunks.

Implements weighted scoring based on:
- Similarity score (vector similarity)
- Source trust score (configurable per source type)
- Recency score (newer content scores higher)
- Author authority score (if available)
"""
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class ScoredChunk:
    """A chunk with its scoring breakdown."""
    chunk_id: int
    document_id: int
    content: str
    similarity_score: float
    source_trust_score: float
    recency_score: float
    author_authority_score: float
    final_score: float
    # Metadata
    source_name: str
    source_type: str
    document_title: str
    author: Optional[str]
    source_updated_at: Optional[datetime]
    section_title: Optional[str]
    extra_data: Dict[str, Any] = None

    def __post_init__(self):
        if self.extra_data is None:
            self.extra_data = {}


class TrustScorer:
    """
    Service for computing trust-weighted scores for retrieved chunks.

    The final score is computed as:
        final_score = (
            weight_similarity × similarity_score +
            weight_source_trust × source_trust_score +
            weight_recency × recency_score +
            weight_author_authority × author_authority_score
        )
    """

    # Default source trust scores by type
    DEFAULT_SOURCE_TRUST = {
        "document": 0.8,
        "notion": 0.7,
        "github": 0.6,
        "slack": 0.5,
        "web": 0.4,
    }

    def __init__(
        self,
        weight_similarity: float = None,
        weight_source_trust: float = None,
        weight_recency: float = None,
        weight_author_authority: float = None,
        recency_decay_days: int = 365,
    ):
        """
        Initialize the trust scorer.

        Args:
            weight_similarity: Weight for similarity score (default from settings)
            weight_source_trust: Weight for source trust score
            weight_recency: Weight for recency score
            weight_author_authority: Weight for author authority score
            recency_decay_days: Days after which recency score drops to 0.5
        """
        self.weight_similarity = weight_similarity or settings.rag_weight_similarity
        self.weight_source_trust = weight_source_trust or settings.rag_weight_source_trust
        self.weight_recency = weight_recency or settings.rag_weight_recency
        self.weight_author_authority = weight_author_authority or settings.rag_weight_author_authority
        self.recency_decay_days = recency_decay_days

        # Normalize weights to sum to 1
        total = (
            self.weight_similarity +
            self.weight_source_trust +
            self.weight_recency +
            self.weight_author_authority
        )
        if total > 0:
            self.weight_similarity /= total
            self.weight_source_trust /= total
            self.weight_recency /= total
            self.weight_author_authority /= total

    def score_chunks(
        self,
        chunks: List[Dict[str, Any]],
        similarity_scores: List[float],
    ) -> List[ScoredChunk]:
        """
        Score a list of retrieved chunks.

        Args:
            chunks: List of chunk dicts with metadata
            similarity_scores: Corresponding similarity scores

        Returns:
            List of ScoredChunk objects sorted by final score descending
        """
        if len(chunks) != len(similarity_scores):
            raise ValueError("Chunks and similarity scores must have same length")

        scored_chunks = []
        for chunk, sim_score in zip(chunks, similarity_scores):
            scored = self._score_chunk(chunk, sim_score)
            scored_chunks.append(scored)

        # Sort by final score descending
        scored_chunks.sort(key=lambda x: x.final_score, reverse=True)
        return scored_chunks

    def _score_chunk(
        self,
        chunk: Dict[str, Any],
        similarity_score: float
    ) -> ScoredChunk:
        """
        Compute scores for a single chunk.

        Args:
            chunk: Chunk dict with metadata
            similarity_score: Vector similarity score (0-1)

        Returns:
            ScoredChunk with all scores computed
        """
        # Get source trust score
        source_type = chunk.get('source_type', 'document').lower()
        base_source_trust = self._get_source_trust(source_type)
        custom_source_trust = chunk.get('source_base_trust_score')
        source_trust = custom_source_trust if custom_source_trust is not None else base_source_trust

        # Compute recency score
        source_updated = chunk.get('source_updated_at')
        recency_score = self._compute_recency_score(source_updated)

        # Get author authority score
        author_trust = chunk.get('author_trust_score', 0.5)

        # Compute final weighted score
        final_score = (
            self.weight_similarity * similarity_score +
            self.weight_source_trust * source_trust +
            self.weight_recency * recency_score +
            self.weight_author_authority * author_trust
        )

        return ScoredChunk(
            chunk_id=chunk.get('chunk_id'),
            document_id=chunk.get('document_id'),
            content=chunk.get('content', ''),
            similarity_score=similarity_score,
            source_trust_score=source_trust,
            recency_score=recency_score,
            author_authority_score=author_trust,
            final_score=final_score,
            source_name=chunk.get('source_name', 'unknown'),
            source_type=source_type,
            document_title=chunk.get('document_title', 'Untitled'),
            author=chunk.get('author'),
            source_updated_at=source_updated,
            section_title=chunk.get('section_title'),
            extra_data=chunk.get('extra_data', {}),
        )

    def _get_source_trust(self, source_type: str) -> float:
        """Get default trust score for a source type."""
        # Try settings first
        settings_trust = {
            "document": settings.rag_trust_weight_document,
            "notion": settings.rag_trust_weight_notion,
            "github": settings.rag_trust_weight_github,
            "slack": settings.rag_trust_weight_slack,
        }
        return settings_trust.get(source_type, self.DEFAULT_SOURCE_TRUST.get(source_type, 0.5))

    def _compute_recency_score(
        self,
        source_updated: Optional[datetime],
    ) -> float:
        """
        Compute recency score based on document age.

        Uses exponential decay: score = e^(-age_days / decay_days)

        Args:
            source_updated: When the source was last updated

        Returns:
            Recency score (0-1)
        """
        if source_updated is None:
            return 0.5  # Default for unknown age

        now = datetime.utcnow()

        # Handle timezone-aware datetimes
        if source_updated.tzinfo is not None:
            from datetime import timezone
            now = now.replace(tzinfo=timezone.utc)

        age = now - source_updated
        age_days = max(0, age.days)

        # Exponential decay
        import math
        score = math.exp(-age_days / self.recency_decay_days)

        return max(0.1, min(1.0, score))  # Clamp to [0.1, 1.0]

    def explain_score(self, scored_chunk: ScoredChunk) -> str:
        """
        Generate a human-readable explanation of the scoring.

        Args:
            scored_chunk: A scored chunk

        Returns:
            Explanation string
        """
        return (
            f"Score breakdown for '{scored_chunk.document_title}':\n"
            f"  - Similarity: {scored_chunk.similarity_score:.3f} "
            f"(weight: {self.weight_similarity:.1%})\n"
            f"  - Source Trust ({scored_chunk.source_type}): {scored_chunk.source_trust_score:.3f} "
            f"(weight: {self.weight_source_trust:.1%})\n"
            f"  - Recency: {scored_chunk.recency_score:.3f} "
            f"(weight: {self.weight_recency:.1%})\n"
            f"  - Author Authority: {scored_chunk.author_authority_score:.3f} "
            f"(weight: {self.weight_author_authority:.1%})\n"
            f"  Final Score: {scored_chunk.final_score:.3f}"
        )
