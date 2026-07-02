"""
Cache Service — coordinates application caching using Redis.
Provides fallback in-memory cache simulator when Redis instance is unreachable/refused.
"""
import logging
import json
from typing import Any, Optional

try:
    import redis.asyncio as aioredis
    REDIS_INSTALLED = True
except ImportError:
    aioredis = None
    REDIS_INSTALLED = False

from app.config import settings

logger = logging.getLogger("hacklaunch.cache_service")


class CacheService:
    def __init__(self) -> None:
        self.redis_client = None
        self._in_memory_fallback = {}
        
        if REDIS_INSTALLED and settings.REDIS_URL:
            try:
                self.redis_client = aioredis.from_url(
                    settings.REDIS_URL, 
                    encoding="utf-8", 
                    decode_responses=True,
                    socket_timeout=2.0
                )
                logger.info("[CacheService] Configured Redis client connection pool successfully.")
            except Exception as e:
                logger.warning(f"[CacheService] Failed to establish Redis client pool: {e}. Falling back to in-memory cache.")
        else:
            logger.info("[CacheService] Redis URL not specified or package offline. Running in In-Memory simulator cache mode.")

    async def get(self, key: str) -> Optional[Any]:
        """Fetches value from Redis or local in-memory cache."""
        if self.redis_client:
            try:
                val = await self.redis_client.get(key)
                if val:
                    return json.loads(val)
            except Exception as e:
                logger.warning(f"[CacheService] Redis get failed: {e}. Using fallback storage.")
        
        # Local fallback get
        return self._in_memory_fallback.get(key)

    async def set(self, key: str, value: Any, expire_seconds: int = 3600) -> bool:
        """Stores key-value pair in Redis or local in-memory cache."""
        serialized = json.dumps(value)
        if self.redis_client:
            try:
                await self.redis_client.set(key, serialized, ex=expire_seconds)
                return True
            except Exception as e:
                logger.warning(f"[CacheService] Redis set failed: {e}. Using fallback storage.")
        
        # Local fallback set
        self._in_memory_fallback[key] = value
        return True

    async def delete(self, key: str) -> bool:
        """Deletes key-value pair from cache."""
        if self.redis_client:
            try:
                await self.redis_client.delete(key)
                return True
            except Exception as e:
                logger.warning(f"[CacheService] Redis delete failed: {e}. Using fallback storage.")
        
        if key in self._in_memory_fallback:
            del self._in_memory_fallback[key]
            return True
        return False
