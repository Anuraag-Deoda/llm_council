"""
Redis client for caching and rate limiting
"""
import json
import logging
from typing import Optional, Any, Union
from datetime import timedelta
import redis.asyncio as redis
from redis.exceptions import RedisError

from app.config import settings

logger = logging.getLogger(__name__)


class RedisClient:
    """Async Redis client wrapper"""

    def __init__(self):
        self.client: Optional[redis.Redis] = None
        self._pool: Optional[redis.ConnectionPool] = None

    async def connect(self) -> None:
        """Initialize Redis connection pool"""
        try:
            self._pool = redis.ConnectionPool.from_url(
                settings.redis_url,
                max_connections=settings.redis_max_connections,
                socket_timeout=settings.redis_socket_timeout,
                decode_responses=True,
            )
            self.client = redis.Redis(connection_pool=self._pool)

            # Test connection
            await self.client.ping()
            logger.info("Redis connection established")
        except RedisError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.client = None

    async def disconnect(self) -> None:
        """Close Redis connection"""
        if self.client:
            await self.client.close()
            if self._pool:
                await self._pool.disconnect()
            logger.info("Redis connection closed")

    async def get(self, key: str) -> Optional[str]:
        """Get value from Redis"""
        if not self.client:
            return None

        try:
            value = await self.client.get(key)
            return value
        except RedisError as e:
            logger.error(f"Redis GET error for key '{key}': {e}")
            return None

    async def get_json(self, key: str) -> Optional[Any]:
        """Get JSON value from Redis"""
        value = await self.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error for key '{key}': {e}")
                return None
        return None

    async def set(
        self,
        key: str,
        value: Union[str, int, float],
        expire: Optional[int] = None
    ) -> bool:
        """Set value in Redis with optional expiration"""
        if not self.client:
            return False

        try:
            if expire:
                await self.client.setex(key, expire, value)
            else:
                await self.client.set(key, value)
            return True
        except RedisError as e:
            logger.error(f"Redis SET error for key '{key}': {e}")
            return False

    async def set_json(
        self,
        key: str,
        value: Any,
        expire: Optional[int] = None
    ) -> bool:
        """Set JSON value in Redis"""
        try:
            json_value = json.dumps(value)
            return await self.set(key, json_value, expire)
        except (TypeError, ValueError) as e:
            logger.error(f"JSON encode error for key '{key}': {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from Redis"""
        if not self.client:
            return False

        try:
            await self.client.delete(key)
            return True
        except RedisError as e:
            logger.error(f"Redis DELETE error for key '{key}': {e}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        if not self.client:
            return False

        try:
            return await self.client.exists(key) > 0
        except RedisError as e:
            logger.error(f"Redis EXISTS error for key '{key}': {e}")
            return False

    async def incr(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment value"""
        if not self.client:
            return None

        try:
            return await self.client.incrby(key, amount)
        except RedisError as e:
            logger.error(f"Redis INCR error for key '{key}': {e}")
            return None

    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration on key"""
        if not self.client:
            return False

        try:
            await self.client.expire(key, seconds)
            return True
        except RedisError as e:
            logger.error(f"Redis EXPIRE error for key '{key}': {e}")
            return False

    async def ttl(self, key: str) -> Optional[int]:
        """Get TTL for key"""
        if not self.client:
            return None

        try:
            return await self.client.ttl(key)
        except RedisError as e:
            logger.error(f"Redis TTL error for key '{key}': {e}")
            return None

    async def keys(self, pattern: str = "*") -> list:
        """Get keys matching pattern"""
        if not self.client:
            return []

        try:
            return await self.client.keys(pattern)
        except RedisError as e:
            logger.error(f"Redis KEYS error for pattern '{pattern}': {e}")
            return []

    async def flush_db(self) -> bool:
        """Flush current database (use with caution!)"""
        if not self.client:
            return False

        try:
            await self.client.flushdb()
            logger.warning("Redis database flushed")
            return True
        except RedisError as e:
            logger.error(f"Redis FLUSHDB error: {e}")
            return False


# Global Redis client instance
redis_client = RedisClient()


async def get_redis() -> RedisClient:
    """Dependency for getting Redis client"""
    return redis_client
