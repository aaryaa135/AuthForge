from typing import Optional

from app.cache.client import redis_client
import json
from app.cache.keys import RedisKeys


class CacheService:
    """
    Redis cache wrapper.
    """

    def set(
        self,
        key: str,
        value: str,
        ttl: Optional[int] = None,
    ) -> None:
        redis_client.set(
            key,
            value,
            ex=ttl,
        )

    def get(
        self,
        key: str,
    ) -> Optional[str]:
        return redis_client.get(key)

    def delete(
        self,
        key: str,
    ) -> None:
        redis_client.delete(key)

    def exists(
        self,
        key: str,
    ) -> bool:
        return bool(redis_client.exists(key))

    def set_json(
        self,
        key: str,
        value: dict,
        ttl: int = 300,
    ) -> None:
        redis_client.set(
            key,
            json.dumps(value),
            ex=ttl,
        )

    def get_json(
        self,
        key: str,
    ) -> dict | None:
        value = redis_client.get(key)

        if value is None:
            return None

        return json.loads(value)

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
