"""
Trust learning service that dynamically adjusts source trust based on conflict resolutions.

This implements a feedback loop where:
1. Conflict resolutions inform source reliability
2. Trust scores are adjusted based on resolution patterns
3. The system learns which sources to trust over time
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from sqlalchemy import func, and_
from sqlalchemy.orm import Session

from app.database.rag_models import (
    ConflictRecord, DocumentSource, Document, DocumentChunk,
    ConflictStatus, ResolutionType, ResolverType
)

logger = logging.getLogger(__name__)


@dataclass
class TrustAdjustment:
    """Represents a trust score adjustment."""
    source_id: int
    source_name: str
    old_trust: float
    new_trust: float
    delta: float
    reason: str
    conflicts_analyzed: int


@dataclass
class SourceTrustProfile:
    """Complete trust profile for a source."""
    source_id: int
    source_name: str
    base_trust_score: float
    computed_trust_score: float

    # Conflict statistics
    total_conflicts: int
    conflicts_won: int  # Source was preferred
    conflicts_lost: int  # Other source was preferred
    conflicts_invalid: int  # Conflict was invalid
    conflicts_merged: int  # Both sources valid

    # Resolution breakdown
    resolutions_by_type: Dict[str, int]

    # Reliability metrics
    win_rate: float
    reliability_score: float  # Computed from win rate and conflict count

    # Recommendations
    trust_recommendation: str


class TrustLearningService:
    """
    Service for learning and adjusting trust scores based on conflict resolution patterns.

    Key features:
    - Analyzes historical conflict resolutions
    - Computes dynamic trust adjustments
    - Provides source reliability profiles
    - Implements trust decay for sources with frequent conflicts
    """

    # Trust adjustment parameters
    BASE_ADJUSTMENT = 0.02  # Base trust change per conflict
    MAX_ADJUSTMENT = 0.15  # Maximum trust change from learning
    MIN_TRUST = 0.1  # Minimum trust score
    MAX_TRUST = 1.0  # Maximum trust score
    CONFLICT_THRESHOLD = 3  # Minimum conflicts before adjusting
    DECAY_RATE = 0.95  # Trust decay for losing conflicts

    def __init__(
        self,
        base_adjustment: float = None,
        max_adjustment: float = None,
        conflict_threshold: int = None,
    ):
        self.base_adjustment = base_adjustment or self.BASE_ADJUSTMENT
        self.max_adjustment = max_adjustment or self.MAX_ADJUSTMENT
        self.conflict_threshold = conflict_threshold or self.CONFLICT_THRESHOLD

    def compute_trust_adjustment(
        self,
        db: Session,
        source_id: int,
        lookback_days: int = 90
    ) -> Optional[TrustAdjustment]:
        """
        Compute trust adjustment for a source based on conflict resolution history.

        Args:
            db: Database session
            source_id: Source ID to analyze
            lookback_days: How many days of history to consider

        Returns:
            TrustAdjustment or None if insufficient data
        """
        source = db.query(DocumentSource).filter(DocumentSource.id == source_id).first()
        if not source:
            return None

        # Get relevant conflicts for this source
        cutoff_date = datetime.utcnow() - timedelta(days=lookback_days)

        # Get chunk IDs for this source
        chunk_ids = db.query(DocumentChunk.id).join(Document).filter(
            Document.source_id == source_id
        ).subquery()

        # Get resolved conflicts involving this source
        conflicts = db.query(ConflictRecord).filter(
            and_(
                ConflictRecord.status == ConflictStatus.RESOLVED,
                ConflictRecord.resolution_type.isnot(None),
                ConflictRecord.detected_at >= cutoff_date,
                (
                    ConflictRecord.chunk_a_id.in_(chunk_ids) |
                    ConflictRecord.chunk_b_id.in_(chunk_ids)
                )
            )
        ).all()

        if len(conflicts) < self.conflict_threshold:
            return None

        # Analyze outcomes
        wins = 0
        losses = 0
        invalid = 0

        for conflict in conflicts:
            # Determine if this source was involved as chunk_a or chunk_b
            chunk_a_doc = db.query(Document).join(DocumentChunk).filter(
                DocumentChunk.id == conflict.chunk_a_id
            ).first()
            chunk_b_doc = db.query(Document).join(DocumentChunk).filter(
                DocumentChunk.id == conflict.chunk_b_id
            ).first()

            is_source_a = chunk_a_doc and chunk_a_doc.source_id == source_id
            is_source_b = chunk_b_doc and chunk_b_doc.source_id == source_id

            if conflict.resolution_type == ResolutionType.INVALID_CONFLICT:
                invalid += 1
                continue

            if conflict.preferred_chunk_id:
                # Check if this source's chunk was preferred
                preferred_doc = db.query(Document).join(DocumentChunk).filter(
                    DocumentChunk.id == conflict.preferred_chunk_id
                ).first()

                if preferred_doc and preferred_doc.source_id == source_id:
                    wins += 1
                elif is_source_a or is_source_b:
                    losses += 1

        # Calculate trust delta
        total_decided = wins + losses
        if total_decided == 0:
            return None

        win_rate = wins / total_decided

        # Compute adjustment: positive for wins, negative for losses
        # Scale by confidence in the data (more conflicts = more confidence)
        confidence = min(1.0, total_decided / 20)  # Max confidence at 20 conflicts
        raw_adjustment = (win_rate - 0.5) * 2 * self.base_adjustment * confidence

        # Clamp adjustment
        adjustment = max(-self.max_adjustment, min(self.max_adjustment, raw_adjustment))

        new_trust = max(self.MIN_TRUST, min(self.MAX_TRUST, source.base_trust_score + adjustment))

        return TrustAdjustment(
            source_id=source_id,
            source_name=source.name,
            old_trust=source.base_trust_score,
            new_trust=new_trust,
            delta=adjustment,
            reason=f"Win rate: {win_rate:.1%} ({wins}W/{losses}L) from {total_decided} resolved conflicts",
            conflicts_analyzed=len(conflicts),
        )

    def apply_trust_adjustment(
        self,
        db: Session,
        adjustment: TrustAdjustment
    ) -> bool:
        """
        Apply a trust adjustment to a source.

        Args:
            db: Database session
            adjustment: The adjustment to apply

        Returns:
            True if applied successfully
        """
        source = db.query(DocumentSource).filter(
            DocumentSource.id == adjustment.source_id
        ).first()

        if not source:
            return False

        source.base_trust_score = adjustment.new_trust
        source.extra_data = source.extra_data or {}
        source.extra_data["trust_learning"] = {
            "last_adjustment": datetime.utcnow().isoformat(),
            "adjustment_delta": adjustment.delta,
            "reason": adjustment.reason,
            "conflicts_analyzed": adjustment.conflicts_analyzed,
        }

        db.commit()
        logger.info(
            f"Applied trust adjustment to source {adjustment.source_name}: "
            f"{adjustment.old_trust:.3f} -> {adjustment.new_trust:.3f} ({adjustment.delta:+.3f})"
        )
        return True

    def get_source_trust_profile(
        self,
        db: Session,
        source_id: int,
        lookback_days: int = 90
    ) -> Optional[SourceTrustProfile]:
        """
        Get comprehensive trust profile for a source.

        Args:
            db: Database session
            source_id: Source ID to analyze
            lookback_days: How many days of history to consider

        Returns:
            SourceTrustProfile or None if source not found
        """
        source = db.query(DocumentSource).filter(DocumentSource.id == source_id).first()
        if not source:
            return None

        cutoff_date = datetime.utcnow() - timedelta(days=lookback_days)

        # Get chunk IDs for this source
        chunk_ids_query = db.query(DocumentChunk.id).join(Document).filter(
            Document.source_id == source_id
        )
        chunk_ids = [c[0] for c in chunk_ids_query.all()]

        if not chunk_ids:
            return SourceTrustProfile(
                source_id=source_id,
                source_name=source.name,
                base_trust_score=source.base_trust_score,
                computed_trust_score=source.base_trust_score,
                total_conflicts=0,
                conflicts_won=0,
                conflicts_lost=0,
                conflicts_invalid=0,
                conflicts_merged=0,
                resolutions_by_type={},
                win_rate=0.5,
                reliability_score=source.base_trust_score,
                trust_recommendation="Insufficient data for analysis"
            )

        # Get all conflicts involving this source
        conflicts = db.query(ConflictRecord).filter(
            and_(
                ConflictRecord.detected_at >= cutoff_date,
                (
                    ConflictRecord.chunk_a_id.in_(chunk_ids) |
                    ConflictRecord.chunk_b_id.in_(chunk_ids)
                )
            )
        ).all()

        # Analyze conflicts
        wins = 0
        losses = 0
        invalid = 0
        merged = 0
        resolutions_by_type = {}

        for conflict in conflicts:
            if conflict.resolution_type:
                rt = conflict.resolution_type.value
                resolutions_by_type[rt] = resolutions_by_type.get(rt, 0) + 1

            if conflict.status != ConflictStatus.RESOLVED:
                continue

            if conflict.resolution_type == ResolutionType.INVALID_CONFLICT:
                invalid += 1
            elif conflict.resolution_type == ResolutionType.MERGED:
                merged += 1
            elif conflict.preferred_chunk_id:
                if conflict.preferred_chunk_id in chunk_ids:
                    wins += 1
                else:
                    losses += 1

        total_decided = wins + losses
        win_rate = wins / total_decided if total_decided > 0 else 0.5

        # Compute reliability score
        # Base: current trust score
        # Adjustment: win rate deviation from 50% scaled by confidence
        confidence = min(1.0, total_decided / 10)
        reliability = source.base_trust_score + (win_rate - 0.5) * 0.2 * confidence
        reliability = max(0.1, min(1.0, reliability))

        # Generate recommendation
        if total_decided < 3:
            recommendation = "Insufficient conflict data for meaningful analysis"
        elif win_rate >= 0.7:
            recommendation = "Highly reliable source - consider increasing trust score"
        elif win_rate >= 0.5:
            recommendation = "Average reliability - current trust score appropriate"
        elif win_rate >= 0.3:
            recommendation = "Below average reliability - consider decreasing trust score"
        else:
            recommendation = "Low reliability - review source quality and consider removal"

        return SourceTrustProfile(
            source_id=source_id,
            source_name=source.name,
            base_trust_score=source.base_trust_score,
            computed_trust_score=reliability,
            total_conflicts=len(conflicts),
            conflicts_won=wins,
            conflicts_lost=losses,
            conflicts_invalid=invalid,
            conflicts_merged=merged,
            resolutions_by_type=resolutions_by_type,
            win_rate=win_rate,
            reliability_score=reliability,
            trust_recommendation=recommendation,
        )

    def resolve_conflict_with_learning(
        self,
        db: Session,
        conflict_id: int,
        resolution_type: ResolutionType,
        resolver_type: ResolverType,
        preferred_chunk_id: Optional[int] = None,
        resolution_notes: Optional[str] = None,
        resolution_confidence: float = 0.8,
        resolved_by: Optional[str] = None,
    ) -> Tuple[ConflictRecord, Optional[TrustAdjustment], Optional[TrustAdjustment]]:
        """
        Resolve a conflict and optionally apply trust learning.

        Args:
            db: Database session
            conflict_id: Conflict to resolve
            resolution_type: How it was resolved
            resolver_type: Who resolved it (human, system, llm)
            preferred_chunk_id: Which chunk is preferred (if applicable)
            resolution_notes: Human-readable notes
            resolution_confidence: Confidence in the resolution (0-1)
            resolved_by: Username/identifier of resolver

        Returns:
            Tuple of (updated conflict, source_a adjustment, source_b adjustment)
        """
        conflict = db.query(ConflictRecord).filter(ConflictRecord.id == conflict_id).first()
        if not conflict:
            raise ValueError(f"Conflict {conflict_id} not found")

        # Update conflict record
        conflict.status = ConflictStatus.RESOLVED
        conflict.resolution_type = resolution_type
        conflict.resolver_type = resolver_type
        conflict.preferred_chunk_id = preferred_chunk_id
        conflict.resolution_notes = resolution_notes
        conflict.resolution_confidence = resolution_confidence
        conflict.resolved_by = resolved_by
        conflict.resolved_at = datetime.utcnow()

        db.commit()

        # Compute potential trust adjustments
        chunk_a_doc = db.query(Document).join(DocumentChunk).filter(
            DocumentChunk.id == conflict.chunk_a_id
        ).first()
        chunk_b_doc = db.query(Document).join(DocumentChunk).filter(
            DocumentChunk.id == conflict.chunk_b_id
        ).first()

        adjustment_a = None
        adjustment_b = None

        if chunk_a_doc:
            adjustment_a = self.compute_trust_adjustment(db, chunk_a_doc.source_id)

        if chunk_b_doc and (not chunk_a_doc or chunk_b_doc.source_id != chunk_a_doc.source_id):
            adjustment_b = self.compute_trust_adjustment(db, chunk_b_doc.source_id)

        return conflict, adjustment_a, adjustment_b

    def run_trust_learning_batch(
        self,
        db: Session,
        min_conflicts: int = 5,
        auto_apply: bool = False
    ) -> List[TrustAdjustment]:
        """
        Run trust learning for all sources with sufficient conflict data.

        Args:
            db: Database session
            min_conflicts: Minimum conflicts required to adjust
            auto_apply: Whether to automatically apply adjustments

        Returns:
            List of computed (and optionally applied) adjustments
        """
        sources = db.query(DocumentSource).filter(DocumentSource.is_active == True).all()
        adjustments = []

        for source in sources:
            adjustment = self.compute_trust_adjustment(db, source.id)
            if adjustment and abs(adjustment.delta) > 0.005:  # Only if meaningful change
                adjustments.append(adjustment)
                if auto_apply:
                    self.apply_trust_adjustment(db, adjustment)

        return adjustments
