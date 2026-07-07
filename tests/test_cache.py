import uuid

from app.cache.service import CacheService


def test_cache_service():
    cache = CacheService()

    key = f"test:{uuid.uuid4()}"

    cache.set_json(
        key,
        {"hello": "world"},
        ttl=60,
    )

    assert cache.get_json(key)["hello"] == "world"

    cache.delete(key)

    assert cache.get_json(key) is None
