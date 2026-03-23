from shared.database import get_db
from shared.config import settings
import redis.asyncio as redis

async def get_redis():
    """Dependency для получения Redis клиента"""
    client = await redis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True
    )
    try:
        yield client
    finally:
        await client.close()