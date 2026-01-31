"""
Rate limiting service using Redis
"""
import logging
import time
from typing import Optional, Tuple
from datetime import datetime, timedelta

from fastapi import Request, HTTPException, status
from app.config import settings
from app.core.redis_client import redis_client

logger = logging.getLogger(__name__)


class RateLimiter:
    """Token bucket rate limiter using Redis"""

    def __init__(self):
        self.enabled = settings.enable_rate_limiting
        self.max_requests = settings.rate_limit_requests
        self.window_seconds = settings.rate_limit_window_seconds
        self.burst_allowance = settings.rate_limit_burst

    def _get_identifier(self, request: Request) -> str:
        """Get unique identifier for rate limiting (IP address or user ID)"""
        # Try to get user ID from headers (if authenticated)
        user_id = request.headers.get("X-User-ID")
        if user_id:
            return f"user:{user_id}"

        # Fall back to IP address
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            ip = forwarded.split(",")[0].strip()
        else:
            ip = request.client.host if request.client else "unknown"

        return f"ip:{ip}"

    def _get_rate_limit_key(self, identifier: str, endpoint: str) -> str:
        """Generate Redis key for rate limiting"""
        return f"ratelimit:{identifier}:{endpoint}"

    async def check_rate_limit(
        self,
        request: Request,
        endpoint: Optional[str] = None
    ) -> Tuple[bool, dict]:
        """
        Check if request is within rate limit

        Returns:
            (is_allowed, metadata) - tuple with boolean and metadata dict
        """
        if not self.enabled:
            return True, {"rate_limit_enabled": False}

        # Get identifier
        identifier = self._get_identifier(request)

        # Get endpoint
        if not endpoint:
            endpoint = request.url.path

        # Generate key
        key = self._get_rate_limit_key(identifier, endpoint)

        try:
            # Get current count
            current_count = await redis_client.get(key)

            if current_count is None:
                # First request in window
                await redis_client.set(key, 1, expire=self.window_seconds)
                return True, {
                    "rate_limit_enabled": True,
                    "requests_made": 1,
                    "requests_limit": self.max_requests,
                    "window_seconds": self.window_seconds,
                    "reset_time": int(time.time()) + self.window_seconds,
                }

            current_count = int(current_count)

            # Check if within limit (including burst)
            if current_count < (self.max_requests + self.burst_allowance):
                # Increment counter
                await redis_client.incr(key)

                # Get TTL for reset time
                ttl = await redis_client.ttl(key)
                reset_time = int(time.time()) + (ttl if ttl > 0 else self.window_seconds)

                return True, {
                    "rate_limit_enabled": True,
                    "requests_made": current_count + 1,
                    "requests_limit": self.max_requests,
                    "window_seconds": self.window_seconds,
                    "reset_time": reset_time,
                }

            # Rate limit exceeded
            ttl = await redis_client.ttl(key)
            reset_time = int(time.time()) + (ttl if ttl > 0 else self.window_seconds)

            return False, {
                "rate_limit_enabled": True,
                "requests_made": current_count,
                "requests_limit": self.max_requests,
                "window_seconds": self.window_seconds,
                "reset_time": reset_time,
                "error": "Rate limit exceeded",
            }

        except Exception as e:
            logger.error(f"Rate limit check error: {e}")
            # On error, allow the request (fail open)
            return True, {"rate_limit_enabled": True, "error": str(e)}

    async def reset_rate_limit(self, identifier: str, endpoint: str) -> bool:
        """Reset rate limit for an identifier and endpoint"""
        key = self._get_rate_limit_key(identifier, endpoint)
        return await redis_client.delete(key)

    async def get_rate_limit_info(self, identifier: str, endpoint: str) -> dict:
        """Get current rate limit information"""
        key = self._get_rate_limit_key(identifier, endpoint)

        current_count = await redis_client.get(key)
        ttl = await redis_client.ttl(key)

        if current_count is None:
            return {
                "requests_made": 0,
                "requests_limit": self.max_requests,
                "window_seconds": self.window_seconds,
                "reset_time": None,
            }

        reset_time = int(time.time()) + (ttl if ttl > 0 else 0)

        return {
            "requests_made": int(current_count),
            "requests_limit": self.max_requests,
            "window_seconds": self.window_seconds,
            "reset_time": reset_time,
        }


# Global rate limiter instance
rate_limiter = RateLimiter()


async def rate_limit_dependency(request: Request) -> None:
    """
    FastAPI dependency for rate limiting

    Usage:
        @app.get("/", dependencies=[Depends(rate_limit_dependency)])
        async def endpoint():
            ...
    """
    is_allowed, metadata = await rate_limiter.check_rate_limit(request)

    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "Rate limit exceeded",
                "requests_made": metadata.get("requests_made"),
                "requests_limit": metadata.get("requests_limit"),
                "reset_time": metadata.get("reset_time"),
                "window_seconds": metadata.get("window_seconds"),
            },
            headers={
                "X-RateLimit-Limit": str(metadata.get("requests_limit")),
                "X-RateLimit-Remaining": str(
                    max(0, metadata.get("requests_limit", 0) - metadata.get("requests_made", 0))
                ),
                "X-RateLimit-Reset": str(metadata.get("reset_time", "")),
            }
        )
