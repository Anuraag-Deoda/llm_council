"""
Caching service with Redis and database fallback
"""
import hashlib
import json
import logging
from typing import Optional, Any, Dict
from datetime import datetime, timedelta

from app.config import settings
from app.core.redis_client import redis_client
from app.database.repositories import CacheRepository

logger = logging.getLogger(__name__)


class CacheService:
    """Multi-tier caching service"""

    def __init__(self):
        self.enabled = settings.enable_cache
        self.default_ttl = settings.cache_ttl_seconds

    @staticmethod
    def generate_cache_key(
        model_id: str,
        prompt: str,
        **kwargs
    ) -> str:
        """Generate cache key from model and prompt"""
        # Create deterministic hash of prompt and parameters
        param_str = json.dumps(kwargs, sort_keys=True)
        content = f"{model_id}:{prompt}:{param_str}"
        hash_value = hashlib.sha256(content.encode()).hexdigest()
        return f"llm_cache:{model_id}:{hash_value[:16]}"

    @staticmethod
    def generate_prompt_hash(prompt: str, **kwargs) -> str:
        """Generate hash of prompt for database"""
        param_str = json.dumps(kwargs, sort_keys=True)
        content = f"{prompt}:{param_str}"
        return hashlib.sha256(content.encode()).hexdigest()

    async def get(
        self,
        cache_key: str,
        db_repository: Optional[CacheRepository] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached response
        Tries Redis first, then database
        """
        if not self.enabled:
            return None

        # Try Redis first (fast)
        redis_value = await redis_client.get_json(cache_key)
        if redis_value:
            logger.debug(f"Cache HIT (Redis): {cache_key}")
            return redis_value

        # Try database (slower but persistent)
        if db_repository:
            db_value = db_repository.get(cache_key)
            if db_value:
                logger.debug(f"Cache HIT (DB): {cache_key}")
                # Populate Redis for future requests
                await redis_client.set_json(
                    cache_key,
                    db_value,
                    expire=self.default_ttl
                )
                return db_value

        logger.debug(f"Cache MISS: {cache_key}")
        return None

    async def set(
        self,
        cache_key: str,
        model_id: str,
        prompt: str,
        response_data: Dict[str, Any],
        ttl: Optional[int] = None,
        db_repository: Optional[CacheRepository] = None,
        **kwargs
    ) -> bool:
        """
        Set cached response in both Redis and database
        """
        if not self.enabled:
            return False

        ttl = ttl or self.default_ttl
        success = True

        # Store in Redis (fast access)
        redis_success = await redis_client.set_json(
            cache_key,
            response_data,
            expire=ttl
        )
        if not redis_success:
            logger.warning(f"Failed to cache in Redis: {cache_key}")
            success = False

        # Store in database (persistent)
        if db_repository:
            try:
                prompt_hash = self.generate_prompt_hash(prompt, **kwargs)
                db_repository.set(
                    cache_key=cache_key,
                    model_id=model_id,
                    prompt_hash=prompt_hash,
                    response_data=response_data,
                    ttl_seconds=ttl
                )
            except Exception as e:
                logger.error(f"Failed to cache in database: {e}")
                success = False

        if success:
            logger.debug(f"Cache SET: {cache_key}")

        return success

    async def delete(
        self,
        cache_key: str,
        db_repository: Optional[CacheRepository] = None
    ) -> bool:
        """Delete cache entry from both Redis and database"""
        redis_success = await redis_client.delete(cache_key)

        if db_repository:
            # Database deletion would need to be implemented in repository
            pass

        return redis_success

    async def clear_model_cache(self, model_id: str) -> int:
        """Clear all cache entries for a specific model"""
        pattern = f"llm_cache:{model_id}:*"
        keys = await redis_client.keys(pattern)

        count = 0
        for key in keys:
            if await redis_client.delete(key):
                count += 1

        logger.info(f"Cleared {count} cache entries for model {model_id}")
        return count

    async def clear_all_cache(self) -> bool:
        """Clear all cache entries (use with caution!)"""
        pattern = "llm_cache:*"
        keys = await redis_client.keys(pattern)

        count = 0
        for key in keys:
            if await redis_client.delete(key):
                count += 1

        logger.warning(f"Cleared all cache: {count} entries")
        return True

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        pattern = "llm_cache:*"
        keys = await redis_client.keys(pattern)

        total_entries = len(keys)
        total_size = 0

        # Sample for size estimation
        sample_size = min(100, total_entries)
        if sample_size > 0:
            for key in keys[:sample_size]:
                value = await redis_client.get(key)
                if value:
                    total_size += len(str(value))

            avg_size = total_size / sample_size
            estimated_total_size = avg_size * total_entries
        else:
            estimated_total_size = 0

        return {
            "enabled": self.enabled,
            "total_entries": total_entries,
            "estimated_size_bytes": int(estimated_total_size),
            "default_ttl_seconds": self.default_ttl,
        }


# Global cache service instance
cache_service = CacheService()
