import json
import logging
from functools import wraps
from typing import Any, Callable, Optional

import redis
from redis.exceptions import ConnectionError, RedisError, TimeoutError

from backend.config import settings

logger = logging.getLogger(__name__)


class CacheClient:
    def __init__(self):
        try:
            self.redis_client = redis.from_url(
                settings.redis_url,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2,
                retry_on_timeout=True,
                health_check_interval=30,
            )

            self.redis_client.ping()
            self._cache_available = True
            logger.info("Redis cache connected successfully")
        except (RedisError, ConnectionError) as e:
            logger.warning(f"Redis cache unavailable: {e}. Operating in degraded mode.")
            self.redis_client = None
            self._cache_available = False

    @property
    def is_available(self) -> bool:
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
        import time

        from backend.infrastructure.metrics import (
            track_cache_hit,
            track_cache_miss,
            track_cache_operation,
        )

        if not self.is_available:
            logger.debug(f"Cache unavailable, skipping get for key: {key}")

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

    def set(self, key: str, value: str, ttl: Optional[int] = None) -> bool:
        import time

        from backend.infrastructure.metrics import track_cache_operation

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
        value = self.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to decode JSON from cache key {key}: {e}")
                return None
        return None

    def set_json(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        try:
            json_value = json.dumps(value)
            return self.set(key, json_value, ttl)
        except (TypeError, ValueError) as e:
            logger.error(f"Failed to serialize value for cache key {key}: {e}")
            return False

    def increment(self, key: str, amount: int = 1) -> Optional[int]:
        if not self.is_available:
            return None

        try:
            return self.redis_client.incrby(key, amount)
        except (RedisError, ConnectionError, TimeoutError) as e:
            logger.warning(f"Cache increment failed for key {key}: {e}")
            self._cache_available = False
            return None

    def expire(self, key: str, ttl: int) -> bool:
        if not self.is_available:
            return False

        try:
            self.redis_client.expire(key, ttl)
            return True
        except (RedisError, ConnectionError, TimeoutError) as e:
            logger.warning(f"Cache expire failed for key {key}: {e}")
            self._cache_available = False
            return False


cache_client = CacheClient()


def with_cache(key_prefix: str, ttl: Optional[int] = None, key_builder: Optional[Callable] = None):
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            if key_builder:
                cache_key = f"{key_prefix}:{key_builder(*args, **kwargs)}"
            else:
                args_str = "_".join(str(arg) for arg in args)
                kwargs_str = "_".join(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = f"{key_prefix}:{func.__name__}:{args_str}:{kwargs_str}"

            cached_value = cache_client.get_json(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_value

            logger.debug(f"Cache miss for {cache_key}, executing function")
            result = func(*args, **kwargs)

            cache_client.set_json(cache_key, result, ttl)

            return result

        return wrapper

    return decorator


def get_cache_status() -> dict:
    status = {
        "available": cache_client.is_available,
        "degraded_mode": not cache_client.is_available,
    }

    if cache_client.is_available and cache_client.redis_client:
        try:
            info = cache_client.redis_client.info()
            status.update(
                {
                    "connected_clients": info.get("connected_clients", 0),
                    "used_memory_human": info.get("used_memory_human", "unknown"),
                    "uptime_in_seconds": info.get("uptime_in_seconds", 0),
                }
            )
        except (RedisError, ConnectionError, TimeoutError):
            status["available"] = False
            status["degraded_mode"] = True

    return status
