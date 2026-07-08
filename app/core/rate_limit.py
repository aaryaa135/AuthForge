from app.cache.service import CacheService


class RateLimiter:
    """
    Redis-based fixed window rate limiter.
    """

    def __init__(self):
        self.cache = CacheService()

    def allow_request(
        self,
        key: str,
        limit: int,
        window: int,
    ) -> bool:
        current = self.cache.get(key)

        if current is None:
            self.cache.set(
                key,
                "1",
                ttl=window,
            )
            return True

        current = int(current)

        if current >= limit:
            return False

        self.cache.set(
            key,
            str(current + 1),
            ttl=window,
        )

        return True
