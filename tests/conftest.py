import os

from fastapi.testclient import TestClient

# Use fakeredis when real Redis is unavailable (CI without redis or local dev without docker)
# Set USE_FAKE_REDIS=1 or let auto-fallback handle connection errors
try:
    import fakeredis

    from app.cache import client as cache_client

    # If REDIS_HOST is unreachable or USE_FAKE_REDIS env, replace with fake
    if os.getenv("USE_FAKE_REDIS") == "1":
        cache_client.redis_client = fakeredis.FakeRedis(decode_responses=True)
    else:
        # Lazy fallback: try ping, swap on failure
        try:
            cache_client.redis_client.ping()
        except Exception:
            cache_client.redis_client = fakeredis.FakeRedis(decode_responses=True)
except ImportError:
    pass

from app.main import app  # noqa: E402

client = TestClient(app)
