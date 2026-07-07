from app.cache.service import CacheService


def test_redis_connection():
    cache = CacheService()

    cache.set(
        "health",
        "ok",
        ttl=10,
    )

    assert cache.get("health") == "ok"

    assert cache.exists("health")

    cache.delete("health")

    assert cache.get("health") is None
