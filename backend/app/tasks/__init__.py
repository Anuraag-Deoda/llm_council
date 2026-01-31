"""
Background tasks with Celery
"""
from .celery_app import celery_app
from .scheduled_tasks import (
    cleanup_expired_cache,
    aggregate_model_analytics,
    health_check_models,
)

__all__ = [
    "celery_app",
    "cleanup_expired_cache",
    "aggregate_model_analytics",
    "health_check_models",
]
