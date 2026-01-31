"""
Scheduled background tasks
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

from celery import Task

from app.tasks.celery_app import celery_app
from app.database.session import SessionLocal
from app.database.repositories import (
    CacheRepository, ModelRepository, AnalyticsRepository
)
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)


class DatabaseTask(Task):
    """Base task with database session"""
    _db = None

    @property
    def db(self):
        if self._db is None:
            self._db = SessionLocal()
        return self._db

    def after_return(self, *args, **kwargs):
        if self._db is not None:
            self._db.close()
            self._db = None


@celery_app.task(base=DatabaseTask, bind=True, name="app.tasks.scheduled_tasks.cleanup_expired_cache")
def cleanup_expired_cache(self):
    """
    Cleanup expired cache entries from database
    Runs every hour
    """
    try:
        logger.info("Starting cache cleanup task...")

        cache_repo = CacheRepository(self.db)

        # Delete expired cache entries
        deleted_count = cache_repo.delete_expired()

        logger.info(f"Cache cleanup completed: {deleted_count} entries deleted")

        return {
            "status": "success",
            "deleted_count": deleted_count,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Cache cleanup task failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@celery_app.task(base=DatabaseTask, bind=True, name="app.tasks.scheduled_tasks.aggregate_model_analytics")
def aggregate_model_analytics(self):
    """
    Aggregate model analytics into hourly buckets
    Runs every hour at :30
    """
    try:
        logger.info("Starting model analytics aggregation task...")

        model_repo = ModelRepository(self.db)
        analytics_repo = AnalyticsRepository(self.db)

        # Get all active models
        models = model_repo.get_all_active()

        aggregated_count = 0

        # Current hour timestamp (rounded down)
        current_hour = datetime.utcnow().replace(minute=0, second=0, microsecond=0)

        for model in models:
            try:
                # Aggregate metrics for this model
                metrics = {
                    "request_count": 0,  # Would be calculated from recent data
                    "error_count": 0,
                    "success_rate": 0.0,
                    "avg_latency_ms": model.avg_latency_ms or 0.0,
                    "total_tokens": 0,
                    "total_cost": 0.0,
                }

                # Create aggregated analytics entry
                analytics_repo.create_model_analytics(
                    model_id=model.id,
                    timestamp=current_hour,
                    metrics=metrics
                )

                aggregated_count += 1

            except Exception as e:
                logger.error(f"Failed to aggregate analytics for model {model.id}: {e}")
                continue

        logger.info(f"Model analytics aggregation completed: {aggregated_count} models processed")

        return {
            "status": "success",
            "aggregated_count": aggregated_count,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Model analytics aggregation task failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@celery_app.task(base=DatabaseTask, bind=True, name="app.tasks.scheduled_tasks.health_check_models")
def health_check_models(self):
    """
    Health check all configured models
    Runs every 5 minutes
    """
    try:
        logger.info("Starting model health check task...")

        model_repo = ModelRepository(self.db)

        # Get all active models
        models = model_repo.get_all_active()

        health_status = {
            "healthy": [],
            "unhealthy": [],
            "total": len(models)
        }

        for model in models:
            try:
                # Simple health check: verify model is configured
                # In production, you might want to make a test API call
                if model.id and model.is_active:
                    health_status["healthy"].append(model.id)
                else:
                    health_status["unhealthy"].append(model.id)

            except Exception as e:
                logger.error(f"Health check failed for model {model.id}: {e}")
                health_status["unhealthy"].append(model.id)

        logger.info(
            f"Model health check completed: "
            f"{len(health_status['healthy'])} healthy, "
            f"{len(health_status['unhealthy'])} unhealthy"
        )

        return {
            "status": "success",
            "health_status": health_status,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Model health check task failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@celery_app.task(name="app.tasks.scheduled_tasks.process_council_async")
def process_council_async(
    conversation_id: str,
    user_query: str,
    model_ids: list
) -> Dict[str, Any]:
    """
    Process council deliberation asynchronously
    Can be triggered manually for long-running council sessions
    """
    try:
        logger.info(f"Starting async council processing for conversation {conversation_id}")

        # This would call the council orchestrator
        # For now, just return a placeholder

        return {
            "status": "success",
            "conversation_id": conversation_id,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Async council processing failed: {e}")
        return {
            "status": "error",
            "conversation_id": conversation_id,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@celery_app.task(name="app.tasks.scheduled_tasks.export_conversation")
def export_conversation(conversation_id: str, format: str = "json") -> Dict[str, Any]:
    """
    Export conversation data in specified format
    Runs asynchronously for large conversations
    """
    try:
        logger.info(f"Exporting conversation {conversation_id} to {format}")

        # Export logic would go here

        return {
            "status": "success",
            "conversation_id": conversation_id,
            "format": format,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Conversation export failed: {e}")
        return {
            "status": "error",
            "conversation_id": conversation_id,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
