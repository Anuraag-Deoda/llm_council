"""
Background tasks with Celery
"""
from .celery_app import celery_app
from .scheduled_tasks import (
    cleanup_expired_cache,
    aggregate_model_analytics,
    health_check_models,
)
from .rag_tasks import (
    ingest_document_task,
    sync_source_task,
    sync_all_sources_task,
    cleanup_orphan_embeddings_task,
    reindex_document_task,
)

__all__ = [
    "celery_app",
    # Scheduled tasks
    "cleanup_expired_cache",
    "aggregate_model_analytics",
    "health_check_models",
    # RAG tasks
    "ingest_document_task",
    "sync_source_task",
    "sync_all_sources_task",
    "cleanup_orphan_embeddings_task",
    "reindex_document_task",
]
