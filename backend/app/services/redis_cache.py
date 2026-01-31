import redis
import json
import hashlib
import os
from typing import Any, Optional
from app.core.observability import cache_hit_counter, cache_miss_counter

# Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
CACHE_TTL = 3600  # 1 hour default


class CacheService:
    def __init__(self):
        self.client = redis.Redis.from_url(REDIS_URL, decode_responses=True)

    def _generate_key(self, prefix: str, data: str) -> str:
        """Creates a hashed key to prevent collision and handle long strings."""
        hash_val = hashlib.sha256(data.encode()).hexdigest()
        return f"{prefix}:{hash_val}"

    def get(self, key: str) -> Optional[Any]:
        """Retrieves data and updates observability metrics."""
        try:
            value = self.client.get(key)
            if value:
                cache_hit_counter.add(1)  # Tracks successful cache usage
                return json.loads(value)

            cache_miss_counter.add(1)  # Tracks when system had to go to the API/DB
            return None
        except redis.RedisError:
            return None

    def set(self, key: str, value: Any, ttl: int = CACHE_TTL):
        """Stores data in Redis with an expiration time."""
        try:
            self.client.setex(key, ttl, json.dumps(value))
        except redis.RedisError:
            pass  # In production, we log this but don't crash the app
