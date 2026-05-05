"""
Redis Cache Infrastructure with Graceful Degradation
Provides caching functionality with fallback to database when cache is unavailable

import logging
import json
from typing import Optional, Any, Callable
from functools import wraps
import redis
from redis.exceptions import RedisError, ConnectionError, TimeoutError

from backend.config import settings

logger = logging.getLogger(__name__)


class CacheClient:
    """
    Redis cache client with graceful degradation
    
    - 22.4: Return cached results within 50ms when available
    - 30.1: Serve requests from database when cache is unavailable
    """
    
    def __init__(self):
        """Initialize Redis client with connection pooling"""
        try:
            self.redis_client = redis.from_url(
                settings.redis_url,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2,
                retry_on_timeout=True,
                health_check_interval=30,
            )
            # Test connection
            self.redis_client.ping()
            self._cache_available = True
            logger.info("Redis cache connected successfully")
        except (RedisError, ConnectionError) as e:
            logger.warning(f"Redis cache unavailable: {e}. Operating in degraded mode.")
            self.redis_client = None
            self._cache_available = False
    
    @property
    def is_available(self) -> bool:
        """Check if cache is currently available"""
        if not self._cache_available:
            return False
        
        try:
            if self.redis_client:
                self.redis_client.ping()
                return True
        except (RedisError, ConnectionError, TimeoutError):
            logger.warning("Cache health check failed. Marking as unavailable.")
            self._cache_available = False
        
        return False
    
    def get(self, key: str) -> Optional[str]:
        """
        Get value from cache
        
        Args:
            key: Cache key
        
        Returns:
            Cached value or None if not found or cache unavailable
        
        Requirement 30.1: Return None when cache unavailable (triggers DB fallback)
        Requirement 21.5: Track cache hit/miss metrics
        """
        from backend.infrastructure.metrics import track_cache_hit, track_cache_miss, track_cache_operation
        import time
        
        if not self.is_available:
            logger.debug(f"Cache unavailable, skipping get for key: {key}")
            # Track as miss when cache is unavailable
            key_prefix = key.split(":")[0] if ":" in key else "unknown"
            track_cache_miss(key_prefix)
            return None
        
        start_time = time.time()
        try:
            value = self.redis_client.get(key)
            duration = time.time() - start_time
            track_cache_operation("get", duration)
            
            key_prefix = key.split(":")[0] if ":" in key else "unknown"
            if value:
                logger.debug(f"Cache hit for key: {key}")
                track_cache_hit(key_prefix)
            else:
                track_cache_miss(key_prefix)
            return value
        except (RedisError, ConnectionError, TimeoutError) as e:
            duration = time.time() - start_time
            track_cache_operation("get", duration)
            logger.warning(f"Cache get failed for key {key}: {e}. Falling back to database.")
            self._cache_available = False
            key_prefix = key.split(":")[0] if ":" in key else "unknown"
            track_cache_miss(key_prefix)
            return None
    
    def set(
        self,
        key: str,
        value: str,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set value in cache with optional TTL
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (default: redis_cache_ttl from config)
        
        Returns:
            True if successful, False if cache unavailable
        
        Requirement 30.1: Gracefully handle cache unavailability
        Requirement 21.5: Track cache operation metrics
        """
        from backend.infrastructure.metrics import track_cache_operation
        import time
        
        if not self.is_available:
            logger.debug(f"Cache unavailable, skipping set for key: {key}")
            return False
        
        start_time = time.time()
        try:
            ttl = ttl or settings.redis_cache_ttl
            self.redis_client.setex(key, ttl, value)
            duration = time.time() - start_time
            track_cache_operation("set", duration)
            logger.debug(f"Cache set for key: {key} with TTL: {ttl}s")
            return True
        except (RedisError, ConnectionError, TimeoutError) as e:
            duration = time.time() - start_time
            track_cache_operation("set", duration)
            logger.warning(f"Cache set failed for key {key}: {e}")
            self._cache_available = False
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete value from cache
        
        Args:
            key: Cache key
        
        Returns:
            True if successful, False if cache unavailable
        """
        if not self.is_available:
            logger.debug(f"Cache unavailable, skipping delete for key: {key}")
            return False
        
        try:
            self.redis_client.delete(key)
            logger.debug(f"Cache deleted for key: {key}")
            return True
        except (RedisError, ConnectionError, TimeoutError) as e:
            logger.warning(f"Cache delete failed for key {key}: {e}")
            self._cache_available = False
            return False
    
    def get_json(self, key: str) -> Optional[Any]:
        """
        Get JSON value from cache
        
        Args:
            key: Cache key
        
        Returns:
            Deserialized JSON value or None
        """
        value = self.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to decode JSON from cache key {key}: {e}")
                return None
        return None
    
    def set_json(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set JSON value in cache
        
        Args:
            key: Cache key
            value: Value to serialize and cache
            ttl: Time-to-live in seconds
        
        Returns:
            True if successful, False otherwise
        """
        try:
            json_value = json.dumps(value)
            return self.set(key, json_value, ttl)
        except (TypeError, ValueError) as e:
            logger.error(f"Failed to serialize value for cache key {key}: {e}")
            return False
    
    def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """
        Increment counter in cache
        
        Args:
            key: Cache key
            amount: Amount to increment by
        
        Returns:
            New value or None if cache unavailable
        """
        if not self.is_available:
            return None
        
        try:
            return self.redis_client.incrby(key, amount)
        except (RedisError, ConnectionError, TimeoutError) as e:
            logger.warning(f"Cache increment failed for key {key}: {e}")
            self._cache_available = False
            return None
    
    def expire(self, key: str, ttl: int) -> bool:
        """
        Set expiration on existing key
        
        Args:
            key: Cache key
            ttl: Time-to-live in seconds
        
        Returns:
            True if successful, False otherwise
        """
        if not self.is_available:
            return False
        
        try:
            self.redis_client.expire(key, ttl)
            return True
        except (RedisError, ConnectionError, TimeoutError) as e:
            logger.warning(f"Cache expire failed for key {key}: {e}")
            self._cache_available = False
            return False


# Global cache client instance
cache_client = CacheClient()


def with_cache(
    key_prefix: str,
    ttl: Optional[int] = None,
    key_builder: Optional[Callable] = None
):
    """
    Decorator to cache function results with automatic fallback
    
    - 22.4: Return cached results within 50ms
    - 30.1: Fallback to function execution when cache unavailable
    
    Args:
        key_prefix: Prefix for cache key
        ttl: Time-to-live in seconds
        key_builder: Optional function to build cache key from function args
    
    Example:
        @with_cache(key_prefix="prediction", ttl=3600)
        def get_prediction(model_id: str, input_hash: str):
            # Expensive computation
            return result
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Build cache key
            if key_builder:
                cache_key = f"{key_prefix}:{key_builder(*args, **kwargs)}"
            else:
                # Default: use function name and args
                args_str = "_".join(str(arg) for arg in args)
                kwargs_str = "_".join(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = f"{key_prefix}:{func.__name__}:{args_str}:{kwargs_str}"
            
            # Try to get from cache
            cached_value = cache_client.get_json(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_value
            
            # Cache miss or unavailable - execute function
            logger.debug(f"Cache miss for {cache_key}, executing function")
            result = func(*args, **kwargs)
            
            # Try to cache result
            cache_client.set_json(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


def get_cache_status() -> dict:
    """
    Get cache status for health checks and monitoring
    
    Returns:
        Dictionary with cache availability and stats
    """
    status = {
        "available": cache_client.is_available,
        "degraded_mode": not cache_client.is_available,
    }
    
    if cache_client.is_available and cache_client.redis_client:
        try:
            info = cache_client.redis_client.info()
            status.update({
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_human": info.get("used_memory_human", "unknown"),
                "uptime_in_seconds": info.get("uptime_in_seconds", 0),
            })
        except (RedisError, ConnectionError, TimeoutError):
            status["available"] = False
            status["degraded_mode"] = True
    
    return status
