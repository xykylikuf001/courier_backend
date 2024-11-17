

from fastapi import FastAPI as BaseFastAPI

from redis.client import Redis
from redis.asyncio import Redis as AIRedis


class FastAPI(BaseFastAPI):
    aioredis_instance: AIRedis
    redis_instance: Redis

    def configure(
            self,
            aioredis_instance: AIRedis,
            redis_instance: Redis,
    ):
        self.aioredis_instance = aioredis_instance
        self.redis_instance = redis_instance
