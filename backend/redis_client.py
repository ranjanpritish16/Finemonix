import redis.asyncio as redis
from backend.config import get_settings

settings = get_settings()

redis_client = redis.from_url(
    settings.REDIS_URL,
    decode_responses=False # Keep bytes to use pickle
)
