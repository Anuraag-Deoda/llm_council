"""
Analytics service for tracking performance and usage
"""
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from collections import defaultdict

from sqlalchemy.orm import Session

from app.config import settings
from app.database.repositories import AnalyticsRepository, ModelRepository
from app.core.metrics import (
    record_llm_tokens, record_llm_cost, record_cache_operation,
    council_sessions_total, council_stage_duration_seconds,
    council_models_count, peer_review_rankings
)

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service for analytics tracking and aggregation"""

    def __init__(self):
        self.enabled = settings.enable_analytics

    def track_council_session(
        self,
        db: Session,
        conversation_id: str,
        stage_metrics: Dict[str, float],
        models_used: List[str],
        peer_reviews: List[Dict[str, Any]],
        total_latency_ms: int,
        total_tokens: int,
        total_cost: float
    ) -> None:
        """Track analytics for a council session"""
        if not self.enabled:
            return

        try:
            # Calculate consensus score
            consensus_score = self._calculate_consensus_score(peer_reviews)

            # Process peer review scores
            peer_review_scores = self._process_peer_reviews(peer_reviews)

            # Create analytics repository
            analytics_repo = AnalyticsRepository(db)

            # Store in database
            analytics_repo.create_conversation_analytics({
                "conversation_id": conversation_id,
                "total_latency_ms": total_latency_ms,
                "total_tokens": total_tokens,
                "total_cost": total_cost,
                "models_used": models_used,
                "model_count": len(models_used),
                "peer_review_scores": peer_review_scores,
                "consensus_score": consensus_score,
                "metadata": {
                    "stage_metrics": stage_metrics
                }
            })

            # Update Prometheus metrics
            council_sessions_total.labels(status="completed").inc()
            council_models_count.observe(len(models_used))

            for stage, duration in stage_metrics.items():
                council_stage_duration_seconds.labels(stage=stage).observe(duration / 1000)

            # Track peer review rankings
            for model_id, scores in peer_review_scores.items():
                avg_rank = scores.get("avg_rank", 0)
                if avg_rank > 0:
                    peer_review_rankings.labels(model_id=model_id).observe(avg_rank)

            logger.info(f"Analytics tracked for conversation {conversation_id}")

        except Exception as e:
            logger.error(f"Failed to track council session analytics: {e}")

    def track_individual_chat(
        self,
        db: Session,
        conversation_id: str,
        model_id: str,
        latency_ms: int,
        tokens_used: int,
        cost: float
    ) -> None:
        """Track analytics for an individual chat"""
        if not self.enabled:
            return

        try:
            analytics_repo = AnalyticsRepository(db)

            analytics_repo.create_conversation_analytics({
                "conversation_id": conversation_id,
                "total_latency_ms": latency_ms,
                "total_tokens": tokens_used,
                "total_cost": cost,
                "models_used": [model_id],
                "model_count": 1,
            })

            logger.debug(f"Individual chat analytics tracked: {conversation_id}")

        except Exception as e:
            logger.error(f"Failed to track individual chat analytics: {e}")

    def track_model_performance(
        self,
        db: Session,
        model_id: str,
        provider: str,
        latency_ms: int,
        input_tokens: int,
        output_tokens: int,
        cost: float,
        is_error: bool = False
    ) -> None:
        """Track model performance metrics"""
        if not self.enabled:
            return

        try:
            # Update model statistics in database
            model_repo = ModelRepository(db)

            model_repo.increment_requests(model_id, is_error=is_error)
            if not is_error:
                model_repo.update_avg_latency(model_id, latency_ms)

            # Update Prometheus metrics
            record_llm_tokens(model_id, provider, input_tokens, output_tokens)
            record_llm_cost(model_id, provider, cost)

            logger.debug(f"Model performance tracked: {model_id}")

        except Exception as e:
            logger.error(f"Failed to track model performance: {e}")

    def update_model_analytics_aggregation(
        self,
        db: Session,
        model_id: str,
        timestamp: datetime,
        metrics: Dict[str, Any]
    ) -> None:
        """Update aggregated model analytics (hourly buckets)"""
        if not self.enabled:
            return

        try:
            analytics_repo = AnalyticsRepository(db)

            analytics_repo.create_model_analytics(
                model_id=model_id,
                timestamp=timestamp,
                metrics=metrics
            )

            logger.debug(f"Model analytics aggregation updated: {model_id}")

        except Exception as e:
            logger.error(f"Failed to update model analytics: {e}")

    def get_conversation_insights(
        self,
        db: Session,
        conversation_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get insights for a specific conversation"""
        try:
            analytics_repo = AnalyticsRepository(db)

            analytics_list = analytics_repo.get_conversation_analytics(conversation_id)

            if not analytics_list:
                return None

            # Aggregate metrics
            total_latency = sum(a.total_latency_ms for a in analytics_list)
            total_tokens = sum(a.total_tokens for a in analytics_list)
            total_cost = sum(a.total_cost for a in analytics_list)

            return {
                "conversation_id": conversation_id,
                "total_interactions": len(analytics_list),
                "total_latency_ms": total_latency,
                "avg_latency_ms": total_latency / len(analytics_list),
                "total_tokens": total_tokens,
                "total_cost": total_cost,
                "avg_consensus_score": sum(
                    a.consensus_score for a in analytics_list if a.consensus_score
                ) / len(analytics_list) if analytics_list else 0,
            }

        except Exception as e:
            logger.error(f"Failed to get conversation insights: {e}")
            return None

    def get_model_insights(
        self,
        db: Session,
        model_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Optional[Dict[str, Any]]:
        """Get insights for a specific model"""
        try:
            analytics_repo = AnalyticsRepository(db)
            model_repo = ModelRepository(db)

            # Get model info
            model = model_repo.get_by_id(model_id)
            if not model:
                return None

            # Get time-series analytics
            analytics_list = analytics_repo.get_model_analytics(
                model_id=model_id,
                start_time=start_time,
                end_time=end_time
            )

            if not analytics_list:
                return {
                    "model_id": model_id,
                    "model_name": model.name,
                    "no_data": True
                }

            # Aggregate metrics
            total_requests = sum(a.request_count for a in analytics_list)
            total_errors = sum(a.error_count for a in analytics_list)
            avg_latency = sum(a.avg_latency_ms * a.request_count for a in analytics_list) / total_requests if total_requests > 0 else 0

            return {
                "model_id": model_id,
                "model_name": model.name,
                "total_requests": total_requests,
                "total_errors": total_errors,
                "success_rate": (total_requests - total_errors) / total_requests if total_requests > 0 else 0,
                "avg_latency_ms": avg_latency,
                "total_tokens": sum(a.total_tokens for a in analytics_list),
                "total_cost": sum(a.total_cost for a in analytics_list),
                "avg_peer_review_rank": sum(
                    a.avg_peer_review_rank for a in analytics_list if a.avg_peer_review_rank
                ) / len([a for a in analytics_list if a.avg_peer_review_rank]) if analytics_list else None,
            }

        except Exception as e:
            logger.error(f"Failed to get model insights: {e}")
            return None

    def get_global_insights(self, db: Session) -> Dict[str, Any]:
        """Get global system insights"""
        try:
            analytics_repo = AnalyticsRepository(db)

            global_stats = analytics_repo.get_global_stats()

            return {
                **global_stats,
                "analytics_enabled": self.enabled,
            }

        except Exception as e:
            logger.error(f"Failed to get global insights: {e}")
            return {"error": str(e)}

    @staticmethod
    def _calculate_consensus_score(peer_reviews: List[Dict[str, Any]]) -> float:
        """
        Calculate consensus score (0-1) based on peer review agreement
        Higher score = more agreement on rankings
        """
        if not peer_reviews or len(peer_reviews) < 2:
            return 0.0

        # Collect all rankings for each model
        model_rankings = defaultdict(list)

        for review in peer_reviews:
            for ranking in review.get("rankings", []):
                model_id = ranking.get("model_id")
                rank = ranking.get("rank")
                if model_id and rank:
                    model_rankings[model_id].append(rank)

        # Calculate variance in rankings
        total_variance = 0
        count = 0

        for model_id, ranks in model_rankings.items():
            if len(ranks) < 2:
                continue

            mean_rank = sum(ranks) / len(ranks)
            variance = sum((r - mean_rank) ** 2 for r in ranks) / len(ranks)
            total_variance += variance
            count += 1

        if count == 0:
            return 0.0

        avg_variance = total_variance / count

        # Convert variance to consensus score (lower variance = higher consensus)
        # Normalize assuming max variance of 10
        consensus_score = max(0.0, min(1.0, 1.0 - (avg_variance / 10.0)))

        return round(consensus_score, 3)

    @staticmethod
    def _process_peer_reviews(peer_reviews: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Process peer reviews into aggregated scores per model"""
        model_scores = defaultdict(lambda: {"ranks": [], "count": 0, "top_rankings": 0})

        for review in peer_reviews:
            for ranking in review.get("rankings", []):
                model_id = ranking.get("model_id")
                rank = ranking.get("rank")

                if model_id and rank:
                    model_scores[model_id]["ranks"].append(rank)
                    model_scores[model_id]["count"] += 1
                    if rank == 1:
                        model_scores[model_id]["top_rankings"] += 1

        # Calculate averages
        result = {}
        for model_id, scores in model_scores.items():
            result[model_id] = {
                "avg_rank": sum(scores["ranks"]) / len(scores["ranks"]) if scores["ranks"] else 0,
                "count": scores["count"],
                "top_rankings": scores["top_rankings"],
            }

        return result


# Global analytics service instance
analytics_service = AnalyticsService()
