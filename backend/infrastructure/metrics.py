import logging
from collections import defaultdict

from prometheus_client import Counter, Histogram

logger = logging.getLogger(__name__)

cache_hits_total = Counter(
    "cache_hits_total",
    "Total cache hits",
    ["key_prefix"],
)
cache_misses_total = Counter(
    "cache_misses_total",
    "Total cache misses",
    ["key_prefix"],
)
cache_operation_duration_seconds = Histogram(
    "cache_operation_duration_seconds",
    "Cache operation duration in seconds",
    ["operation"],
)

_fallback_counts: dict[str, int] = defaultdict(int)


def track_cache_hit(key_prefix: str) -> None:
    try:
        cache_hits_total.labels(key_prefix=key_prefix).inc()
    except Exception as exc:
        _fallback_counts[f"hit:{key_prefix}"] += 1
        logger.debug(f"Failed to record cache hit metric: {exc}")


def track_cache_miss(key_prefix: str) -> None:
    try:
        cache_misses_total.labels(key_prefix=key_prefix).inc()
    except Exception as exc:
        _fallback_counts[f"miss:{key_prefix}"] += 1
        logger.debug(f"Failed to record cache miss metric: {exc}")


def track_cache_operation(operation: str, duration: float) -> None:
    try:
        cache_operation_duration_seconds.labels(operation=operation).observe(duration)
    except Exception as exc:
        _fallback_counts[f"operation:{operation}"] += 1
        logger.debug(f"Failed to record cache operation metric: {exc}")
