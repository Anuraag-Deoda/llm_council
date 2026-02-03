"""
Main FastAPI application for LLM Council.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .routes import chat, models, individual, admin, analytics, health, export, rag, auth
from .database import init_db, close_db
from .core.redis_client import redis_client
from .core.metrics import init_metrics, metrics_endpoint

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Application Lifespan
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting LLM Council API...")

    # Initialize database
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")

    # Initialize Redis
    try:
        await redis_client.connect()
        logger.info("Redis connected successfully")
    except Exception as e:
        logger.warning(f"Redis connection failed: {e}")

    # Initialize metrics
    if settings.enable_metrics:
        init_metrics()
        logger.info("Metrics initialized")

    logger.info("LLM Council API started successfully")

    yield

    # Shutdown
    logger.info("Shutting down LLM Council API...")

    # Close Redis
    try:
        await redis_client.disconnect()
        logger.info("Redis disconnected")
    except Exception as e:
        logger.error(f"Redis disconnect error: {e}")

    # Close database
    try:
        close_db()
        logger.info("Database closed")
    except Exception as e:
        logger.error(f"Database close error: {e}")

    logger.info("LLM Council API shut down complete")


# ============================================================================
# Create FastAPI App
# ============================================================================

app = FastAPI(
    title="LLM Council API",
    description="Enterprise-grade backend API for the LLM Council application with advanced features",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Include Routers
# ============================================================================

# Core functionality
app.include_router(chat.router)
app.include_router(models.router)
app.include_router(individual.router)

# Advanced features
app.include_router(admin.router)
app.include_router(analytics.router)
app.include_router(health.router)
app.include_router(export.router)

# RAG (Retrieval-Augmented Generation)
app.include_router(rag.router)

# Authentication
app.include_router(auth.router)


# ============================================================================
# Root Endpoints
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "LLM Council API",
        "version": "1.0.0",
        "status": "running",
        "features": {
            "database": "PostgreSQL",
            "cache": "Redis" if settings.enable_cache else "Disabled",
            "rate_limiting": settings.enable_rate_limiting,
            "metrics": settings.enable_metrics,
            "analytics": settings.enable_analytics,
            "background_tasks": "Celery"
        },
        "endpoints": {
            "docs": "/docs",
            "health": "/health/detailed",
            "metrics": "/metrics",
            "admin": "/admin",
            "analytics": "/analytics",
            "rag": "/rag"
        }
    }


# Prometheus metrics endpoint
if settings.enable_metrics:
    @app.get("/metrics")
    def get_metrics():
        """Prometheus metrics endpoint"""
        return metrics_endpoint()


# ============================================================================
# Error Handlers
# ============================================================================

@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Custom 404 handler"""
    return {
        "detail": "Resource not found",
        "path": str(request.url.path)
    }


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Custom 500 handler"""
    logger.error(f"Internal server error: {exc}")
    return {
        "detail": "Internal server error",
        "message": "An unexpected error occurred"
    }


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=settings.log_level.lower()
    )
