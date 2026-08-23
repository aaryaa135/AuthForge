from app.cache.client import redis_client


class RateLimiter:
    """
    Redis-based fixed window rate limiter (atomic INCR + EXPIRE).
    """

    def allow_request(
        self,
        key: str,
        limit: int,
        window: int,
    ) -> bool:
        # Atomic increment; set expiry only on first hit
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
