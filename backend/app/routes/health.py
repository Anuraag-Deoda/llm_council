"""
Health check and system monitoring endpoints
"""
import time
from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel

from app.database import get_db
from app.core.redis_client import redis_client
from app.config import settings

router = APIRouter(prefix="/health", tags=["health"])


class HealthStatus(BaseModel):
    status: str
    timestamp: datetime
    version: str = "1.0.0"


class DetailedHealthCheck(BaseModel):
    status: str
    timestamp: datetime
    version: str
    components: Dict[str, Any]
    performance: Dict[str, float]


@router.get("/", response_model=HealthStatus)
def health_check():
    """Basic health check endpoint"""
    return HealthStatus(
        status="healthy",
        timestamp=datetime.utcnow()
    )


@router.get("/detailed", response_model=DetailedHealthCheck)
async def detailed_health_check(db: Session = Depends(get_db)):
    """Comprehensive health check with component status"""
    start_time = time.time()

    components = {}

    # Check database
    try:
        db_start = time.time()
        db.execute(text("SELECT 1"))
        db_latency = (time.time() - db_start) * 1000

        components["database"] = {
            "status": "healthy",
            "latency_ms": round(db_latency, 2),
            "url": settings.database_url.split("@")[-1] if "@" in settings.database_url else "configured"
        }
    except Exception as e:
        components["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }

    # Check Redis
    try:
        redis_start = time.time()
        await redis_client.client.ping() if redis_client.client else None
        redis_latency = (time.time() - redis_start) * 1000

        components["redis"] = {
            "status": "healthy" if redis_client.client else "unavailable",
            "latency_ms": round(redis_latency, 2)
        }
    except Exception as e:
        components["redis"] = {
            "status": "unhealthy",
            "error": str(e)
        }

    # Check cache service
    components["cache"] = {
        "status": "enabled" if settings.enable_cache else "disabled",
        "enabled": settings.enable_cache
    }

    # Check rate limiting
    components["rate_limiting"] = {
        "status": "enabled" if settings.enable_rate_limiting else "disabled",
        "enabled": settings.enable_rate_limiting
    }

    # Check metrics
    components["metrics"] = {
        "status": "enabled" if settings.enable_metrics else "disabled",
        "enabled": settings.enable_metrics
    }

    # Check analytics
    components["analytics"] = {
        "status": "enabled" if settings.enable_analytics else "disabled",
        "enabled": settings.enable_analytics
    }

    # Overall status
    overall_status = "healthy"
    if components["database"]["status"] != "healthy":
        overall_status = "degraded"

    # Performance metrics
    total_latency = (time.time() - start_time) * 1000

    performance = {
        "total_check_time_ms": round(total_latency, 2),
        "database_latency_ms": components["database"].get("latency_ms", 0),
        "redis_latency_ms": components["redis"].get("latency_ms", 0)
    }

    return DetailedHealthCheck(
        status=overall_status,
        timestamp=datetime.utcnow(),
        version="1.0.0",
        components=components,
        performance=performance
    )


@router.get("/readiness")
def readiness_check(db: Session = Depends(get_db)):
    """
    Kubernetes readiness probe
    Returns 200 if service is ready to accept traffic
    """
    try:
        # Check if database is accessible
        db.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception as e:
        return {"status": "not_ready", "error": str(e)}, 503


@router.get("/liveness")
def liveness_check():
    """
    Kubernetes liveness probe
    Returns 200 if service is alive
    """
    return {"status": "alive"}


@router.get("/metrics-summary")
async def metrics_summary(db: Session = Depends(get_db)):
    """Get summary of key metrics"""
    from app.database.models import Conversation, Message, ModelInfo

    # Get counts
    total_conversations = db.query(Conversation).count()
    total_messages = db.query(Message).count()
    total_models = db.query(ModelInfo).filter(ModelInfo.is_active == True).count()

    # Get cache stats if available
    cache_stats = {}
    if settings.enable_cache:
        try:
            from app.core.cache_service import cache_service
            cache_stats = await cache_service.get_cache_stats()
        except:
            cache_stats = {"error": "Failed to get cache stats"}

    return {
        "conversations": total_conversations,
        "messages": total_messages,
        "active_models": total_models,
        "cache": cache_stats,
        "features": {
            "caching": settings.enable_cache,
            "rate_limiting": settings.enable_rate_limiting,
            "metrics": settings.enable_metrics,
            "analytics": settings.enable_analytics
        }
    }


@router.get("/config")
def get_configuration():
    """Get non-sensitive configuration"""
    return {
        "max_tokens": settings.max_tokens,
        "temperature": settings.temperature,
        "chairman_model": settings.chairman_model,
        "features": {
            "cache": {
                "enabled": settings.enable_cache,
                "ttl_seconds": settings.cache_ttl_seconds
            },
            "rate_limiting": {
                "enabled": settings.enable_rate_limiting,
                "requests": settings.rate_limit_requests,
                "window_seconds": settings.rate_limit_window_seconds
            },
            "council": {
                "voting_system": settings.default_voting_system,
                "min_models": settings.min_council_models,
                "peer_review": settings.enable_peer_review
            }
        }
    }
