import json
import time

import redis.exceptions

from app.cache.client import redis_client
from app.cache.keys import RedisKeys
from app.core.logger import logger


class CircuitBreaker:
    """
    Simple circuit breaker for Redis resilience.

    After `failure_threshold` consecutive failures, the circuit opens for
    `recovery_timeout` seconds. While open, calls fail fast without hitting Redis.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self._failures = 0
        self._opened_at: float | None = None

    @property
    def is_open(self) -> bool:
        if self._opened_at is None:
            return False
        if time.time() - self._opened_at >= self.recovery_timeout:
            self._opened_at = None
            self._failures = 0
            return False
        return True

    def record_success(self) -> None:
        self._failures = 0
        self._opened_at = None

    def record_failure(self) -> None:
        self._failures += 1
        if self._failures >= self.failure_threshold and self._opened_at is None:
            self._opened_at = time.time()
            logger.warning(
                "Redis circuit breaker opened after %d failures",
                self._failures,
            )


_breaker = CircuitBreaker()


def _redis_call(fn, fallback):
    """
    Execute a Redis call with circuit breaker protection.

    Returns `fallback` when Redis is unavailable or the circuit is open.
    """
    if _breaker.is_open:
        return fallback
    try:
        result = fn()
        _breaker.record_success()
        return result
    except redis.exceptions.RedisError as exc:
        _breaker.record_failure()
        logger.warning("Redis call failed: %s", exc)
        return fallback


class CacheService:
    """
    Redis cache wrapper with graceful degradation.

    When Redis is unavailable, reads return cache misses and writes are
    silently dropped so the auth service keeps operating (fail-safe).
    """

    def set(
        self,
        key: str,
        value: str,
        ttl: int | None = None,
    ) -> None:
        _redis_call(
            lambda: redis_client.set(key, value, ex=ttl),
            None,
        )

    def get(
        self,
        key: str,
    ) -> str | None:
        return _redis_call(
            lambda: redis_client.get(key),
            None,
        )

    def delete(
        self,
        key: str,
    ) -> None:
        _redis_call(
            lambda: redis_client.delete(key),
            None,
        )

    def exists(
        self,
        key: str,
    ) -> bool:
        return bool(_redis_call(lambda: redis_client.exists(key), 0))

    def set_json(
        self,
        key: str,
        value: dict,
        ttl: int = 300,
    ) -> None:
        _redis_call(
            lambda: redis_client.set(key, json.dumps(value), ex=ttl),
            None,
        )

    def get_json(
        self,
        key: str,
    ) -> dict | None:
        value = _redis_call(lambda: redis_client.get(key), None)
        if value is None:
            return None
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return None

    def blacklist_token(
        self,
        jti: str,
        ttl: int,
    ):
        self.set(
            RedisKeys.blacklist(jti),
            "1",
            ttl,
        )

    def is_blacklisted(
        self,
        jti: str,
    ) -> bool:
        return self.exists(RedisKeys.blacklist(jti))
