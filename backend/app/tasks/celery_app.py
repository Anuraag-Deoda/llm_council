"""
Celery application configuration
"""
from celery import Celery
from celery.schedules import crontab

from app.config import settings

# Create Celery app
celery_app = Celery(
    "llm_council",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.tasks.scheduled_tasks"]
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    # Result backend settings
    result_expires=3600,  # Results expire after 1 hour
    result_extended=True,

    # Worker settings
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,

    # Task execution settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_time_limit=600,  # 10 minutes hard limit
    task_soft_time_limit=540,  # 9 minutes soft limit

    # Beat schedule (scheduled tasks)
    beat_schedule={
        # Cleanup expired cache every hour
        "cleanup-expired-cache": {
            "task": "app.tasks.scheduled_tasks.cleanup_expired_cache",
            "schedule": crontab(minute=0),  # Every hour at :00
        },
        # Aggregate analytics every hour
        "aggregate-model-analytics": {
            "task": "app.tasks.scheduled_tasks.aggregate_model_analytics",
            "schedule": crontab(minute=30),  # Every hour at :30
        },
        # Health check models every 5 minutes
        "health-check-models": {
            "task": "app.tasks.scheduled_tasks.health_check_models",
            "schedule": crontab(minute="*/5"),  # Every 5 minutes
        },
    },
)
