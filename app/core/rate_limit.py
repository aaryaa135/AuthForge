import redis.exceptions

from app.cache.client import redis_client
from app.core.logger import logger


class RateLimiter:
    """
    Redis-based fixed window rate limiter (atomic INCR + EXPIRE).

    Fails open (allows the request) when Redis is unavailable so the
    auth service stays operational; failures are logged for alerting.
    """

    def allow_request(
        self,
        key: str,
        limit: int,
        window: int,
    ) -> bool:
        try:
            pipe = redis_client.pipeline()
            pipe.incr(key)
            pipe.ttl(key)
            count, ttl = pipe.execute()

            if count == 1:
                redis_client.expire(key, window)
            elif ttl == -1:
                # Key existed without TTL (edge case) — restore window
                redis_client.expire(key, window)

            return count <= limit

        except redis.exceptions.RedisError as exc:
            logger.warning("Rate limiter Redis failure for key %s: %s", key, exc)
            # Fail open: allow the request when Redis is down
            return True
