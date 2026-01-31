"""
Prometheus metrics for monitoring
"""
import time
import logging
from typing import Optional
from functools import wraps
from contextlib import contextmanager

from prometheus_client import (
    Counter, Histogram, Gauge, Info,
    generate_latest, CONTENT_TYPE_LATEST
)
from fastapi import Response

from app.config import settings

logger = logging.getLogger(__name__)

# ============================================================================
# Request Metrics
# ============================================================================

http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"]
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0)
)

# ============================================================================
# LLM Metrics
# ============================================================================

llm_requests_total = Counter(
    "llm_requests_total",
    "Total LLM API requests",
    ["model_id", "provider", "status"]
)

llm_request_duration_seconds = Histogram(
    "llm_request_duration_seconds",
    "LLM API request duration in seconds",
    ["model_id", "provider"],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0)
)

llm_tokens_total = Counter(
    "llm_tokens_total",
    "Total tokens used",
    ["model_id", "provider", "token_type"]  # token_type: input/output
)

llm_cost_total = Counter(
    "llm_cost_total",
    "Total cost in USD",
    ["model_id", "provider"]
)

llm_errors_total = Counter(
    "llm_errors_total",
    "Total LLM errors",
    ["model_id", "provider", "error_type"]
)

# ============================================================================
# Council Metrics
# ============================================================================

council_sessions_total = Counter(
    "council_sessions_total",
    "Total council sessions",
    ["status"]  # status: completed/failed
)

council_stage_duration_seconds = Histogram(
    "council_stage_duration_seconds",
    "Council stage duration in seconds",
    ["stage"],  # stage: first_opinions/review/final_response
    buckets=(1.0, 5.0, 10.0, 30.0, 60.0, 120.0)
)

council_models_count = Histogram(
    "council_models_count",
    "Number of models in council",
    buckets=(1, 3, 5, 7, 10, 15, 20)
)

peer_review_rankings = Histogram(
    "peer_review_rankings",
    "Peer review ranking distribution",
    ["model_id"],
    buckets=(1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
)

# ============================================================================
# Cache Metrics
# ============================================================================

cache_operations_total = Counter(
    "cache_operations_total",
    "Total cache operations",
    ["operation", "result"]  # operation: get/set/delete, result: hit/miss/error
)

cache_hit_ratio = Gauge(
    "cache_hit_ratio",
    "Cache hit ratio (0-1)"
)

cache_size_bytes = Gauge(
    "cache_size_bytes",
    "Estimated cache size in bytes"
)

# ============================================================================
# Database Metrics
# ============================================================================

db_operations_total = Counter(
    "db_operations_total",
    "Total database operations",
    ["operation", "table", "status"]  # operation: select/insert/update/delete
)

db_operation_duration_seconds = Histogram(
    "db_operation_duration_seconds",
    "Database operation duration in seconds",
    ["operation", "table"],
    buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0)
)

db_connection_pool_size = Gauge(
    "db_connection_pool_size",
    "Current database connection pool size"
)

# ============================================================================
# Rate Limiting Metrics
# ============================================================================

rate_limit_hits_total = Counter(
    "rate_limit_hits_total",
    "Total rate limit hits",
    ["identifier_type", "endpoint"]  # identifier_type: ip/user
)

rate_limit_blocks_total = Counter(
    "rate_limit_blocks_total",
    "Total rate limit blocks",
    ["identifier_type", "endpoint"]
)

# ============================================================================
# System Metrics
# ============================================================================

app_info = Info(
    "app_info",
    "Application information"
)

active_requests = Gauge(
    "active_requests",
    "Number of active requests"
)

websocket_connections = Gauge(
    "websocket_connections",
    "Number of active WebSocket connections"
)

# ============================================================================
# Helper Functions
# ============================================================================

@contextmanager
def track_time(histogram: Histogram, **labels):
    """Context manager for tracking execution time"""
    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        if labels:
            histogram.labels(**labels).observe(duration)
        else:
            histogram.observe(duration)


def track_llm_request(model_id: str, provider: str):
    """Decorator for tracking LLM requests"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"

            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                error_type = type(e).__name__
                llm_errors_total.labels(
                    model_id=model_id,
                    provider=provider,
                    error_type=error_type
                ).inc()
                raise
            finally:
                duration = time.time() - start_time
                llm_requests_total.labels(
                    model_id=model_id,
                    provider=provider,
                    status=status
                ).inc()
                llm_request_duration_seconds.labels(
                    model_id=model_id,
                    provider=provider
                ).observe(duration)

        return wrapper
    return decorator


def record_llm_tokens(model_id: str, provider: str, input_tokens: int, output_tokens: int):
    """Record token usage"""
    llm_tokens_total.labels(
        model_id=model_id,
        provider=provider,
        token_type="input"
    ).inc(input_tokens)

    llm_tokens_total.labels(
        model_id=model_id,
        provider=provider,
        token_type="output"
    ).inc(output_tokens)


def record_llm_cost(model_id: str, provider: str, cost: float):
    """Record LLM API cost"""
    llm_cost_total.labels(
        model_id=model_id,
        provider=provider
    ).inc(cost)


def record_cache_operation(operation: str, result: str):
    """Record cache operation"""
    cache_operations_total.labels(
        operation=operation,
        result=result
    ).inc()


def update_cache_stats(hit_ratio: float, size_bytes: int):
    """Update cache statistics"""
    cache_hit_ratio.set(hit_ratio)
    cache_size_bytes.set(size_bytes)


def record_db_operation(operation: str, table: str, status: str, duration: float):
    """Record database operation"""
    db_operations_total.labels(
        operation=operation,
        table=table,
        status=status
    ).inc()

    db_operation_duration_seconds.labels(
        operation=operation,
        table=table
    ).observe(duration)


def metrics_endpoint():
    """Generate Prometheus metrics endpoint"""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


def init_metrics():
    """Initialize metrics with application info"""
    app_info.info({
        "version": "1.0.0",
        "environment": "production",
    })
    logger.info("Metrics initialized")
