"""
Enterprise caching layer with Redis and disk cache fallback.
Provides consistent caching interface across the application.
"""

import hashlib
import json
import pickle
from abc import ABC, abstractmethod
from functools import wraps
from typing import Any, Callable, Optional, Union
from datetime import timedelta

import diskcache as dc

from src.config import settings


class CacheBackend(ABC):
    """Abstract base class for cache backends."""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with optional TTL."""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        pass
    
    @abstractmethod
    async def clear(self) -> bool:
        """Clear all cache entries."""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        pass


class RedisCacheBackend(CacheBackend):
    """Redis cache backend implementation."""
    
    def __init__(self):
        self._redis = None
        self._available = False
        self._logger = None
        self._initialize_redis()
    
    @property
    def logger(self):
        """Lazy import logger to avoid circular imports."""
        if self._logger is None:
            from src.core.logging import get_logger
            self._logger = get_logger("redis_cache")
        return self._logger
    
    def _initialize_redis(self):
        """Initialize Redis connection."""
        try:
            import redis.asyncio as redis
            self._redis = redis.from_url(settings.redis_url)
            self._available = True
            self.logger.info("Redis cache backend initialized")
        except ImportError:
            self.logger.warning("Redis not available, caching disabled")
        except Exception as e:
            self.logger.error("Failed to initialize Redis", error=str(e))
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from Redis cache."""
        if not self._available:
            return None
        
        try:
            value = await self._redis.get(key)
            if value:
                return pickle.loads(value)
            return None
        except Exception as e:
            self.logger.error("Redis get failed", key=key, error=str(e))
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in Redis cache."""
        if not self._available:
            return False
        
        try:
            serialized = pickle.dumps(value)
            if ttl:
                await self._redis.setex(key, ttl, serialized)
            else:
                await self._redis.set(key, serialized)
            return True
        except Exception as e:
            self.logger.error("Redis set failed", key=key, error=str(e))
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from Redis cache."""
        if not self._available:
            return False
        
        try:
            result = await self._redis.delete(key)
            return result > 0
        except Exception as e:
            self.logger.error("Redis delete failed", key=key, error=str(e))
            return False
    
    async def clear(self) -> bool:
        """Clear all Redis cache entries."""
        if not self._available:
            return False
        
        try:
            await self._redis.flushdb()
            return True
        except Exception as e:
            self.logger.error("Redis clear failed", error=str(e))
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis."""
        if not self._available:
            return False
        
        try:
            result = await self._redis.exists(key)
            return result > 0
        except Exception as e:
            self.logger.error("Redis exists check failed", key=key, error=str(e))
            return False


class DiskCacheBackend(CacheBackend):
    """Disk cache backend implementation using diskcache."""
    
    def __init__(self, cache_dir: str = "./cache"):
        self._cache = dc.Cache(cache_dir)
        self._logger = None
        self.logger.info("Disk cache backend initialized", cache_dir=cache_dir)
    
    @property
    def logger(self):
        """Lazy import logger to avoid circular imports."""
        if self._logger is None:
            from src.core.logging import get_logger
            self._logger = get_logger("disk_cache")
        return self._logger
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from disk cache."""
        try:
            return self._cache.get(key)
        except Exception as e:
            self.logger.error("Disk cache get failed", key=key, error=str(e))
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in disk cache."""
        try:
            if ttl:
                self._cache.set(key, value, expire=ttl)
            else:
                self._cache.set(key, value)
            return True
        except Exception as e:
            self.logger.error("Disk cache set failed", key=key, error=str(e))
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from disk cache."""
        try:
            return self._cache.delete(key)
        except Exception as e:
            self.logger.error("Disk cache delete failed", key=key, error=str(e))
            return False
    
    async def clear(self) -> bool:
        """Clear all disk cache entries."""
        try:
            self._cache.clear()
            return True
        except Exception as e:
            self.logger.error("Disk cache clear failed", error=str(e))
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in disk cache."""
        try:
            return key in self._cache
        except Exception as e:
            self.logger.error("Disk cache exists check failed", key=key, error=str(e))
            return False


class CacheManager:
    """Main cache manager with fallback support."""
    
    def __init__(self):
        self.primary_backend = RedisCacheBackend()
        self.fallback_backend = DiskCacheBackend()
        self.enabled = settings.enable_caching
        self._logger = None
    
    @property
    def logger(self):
        """Lazy import logger to avoid circular imports."""
        if self._logger is None:
            from src.core.logging import get_logger
            self._logger = get_logger("cache_manager")
        return self._logger
    
    def _generate_cache_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate a consistent cache key."""
        key_data = f"{prefix}:{str(args)}:{str(sorted(kwargs.items()))}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache with fallback."""
        if not self.enabled:
            return None
        
        # Try primary backend first
        value = await self.primary_backend.get(key)
        if value is not None:
            self.logger.debug("Cache hit (primary)", key=key)
            return value
        
        # Try fallback backend
        value = await self.fallback_backend.get(key)
        if value is not None:
            self.logger.debug("Cache hit (fallback)", key=key)
            return value
        
        self.logger.debug("Cache miss", key=key)
        return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with fallback."""
        if not self.enabled:
            return False
        
        ttl = ttl or settings.cache_ttl
        
        # Try to set in primary backend
        primary_success = await self.primary_backend.set(key, value, ttl)
        
        # Always set in fallback backend
        fallback_success = await self.fallback_backend.set(key, value, ttl)
        
        self.logger.debug(
            "Cache set",
            key=key,
            primary_success=primary_success,
            fallback_success=fallback_success,
            ttl=ttl
        )
        
        return primary_success or fallback_success


# Global cache manager instance
cache = CacheManager()


def cached(
    prefix: str = "default",
    ttl: Optional[int] = None,
    key_func: Optional[Callable] = None
):
    """Decorator for caching function results."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if not settings.enable_caching:
                return await func(*args, **kwargs)
            
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = cache._generate_cache_key(f"{prefix}:{func.__name__}", *args, **kwargs)
            
            # Try to get from cache
            cached_result = await cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator 