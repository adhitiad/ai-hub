# src/core/redis_client.py
import asyncio
import json
import os
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from redis import asyncio as aioredis

from src.core.logger import logger

load_dotenv()


class RedisManager:
    def __init__(self):
        self.redis_url = os.getenv(
            "REDIS_URL",
            f"redis://{os.getenv('REDIS_USER')}:{os.getenv('REDIS_PASSWORD')}@{os.getenv('REDIS_HOST')}:{os.getenv('REDIS_PORT')}/0",
        )
        self.redis = None

    async def connect(self):
        if not self.redis:
            self.redis = await aioredis.from_url(
                self.redis_url, encoding="utf-8", decode_responses=True
            )
            logger.info("✅ Redis Connected")

    async def close(self):
        if self.redis:
            await self.redis.close()
            logger.info("🔒 Redis Closed")

    async def set_signal(self, symbol: str, data: dict) -> None:
        """Simpan sinyal dan Publish event"""
        if not self.redis:
            await self.connect()

        # Use type assertion to tell Pylance that redis is not None after connect
        redis_conn = self.redis
        if redis_conn:
            # 1. Simpan data (Persistence)
            hset_result: int = await redis_conn.hset(  # type: ignore[misc]
                "market_signals", symbol, json.dumps(data)
            )

            # 2. Publish event real-time (Pub/Sub)
            # Channel khusus per simbol dan channel global
            publish_result1: int = await redis_conn.publish(
                f"signal:{symbol}", json.dumps(data)
            )
            publish_result2: int = await redis_conn.publish(
                "signal:all", json.dumps(data)
            )

    async def get_signal(self, symbol: str) -> Optional[Dict[str, Any]]:
        if not self.redis:
            await self.connect()

        redis_conn = self.redis
        if redis_conn:
            data = await redis_conn.hget("market_signals", symbol)  # type: ignore[misc]
            return json.loads(data) if data else None
        return None

    async def get_all_signals(self) -> Dict[str, Dict[str, Any]]:
        if not self.redis:
            await self.connect()

        redis_conn = self.redis
        if redis_conn:
            all_data = await redis_conn.hgetall("market_signals")  # type: ignore[misc]
            return {k: json.loads(v) for k, v in all_data.items()}
        return {}

    async def get(self, key: str) -> Optional[str]:
        if not self.redis:
            await self.connect()

        redis_conn = self.redis
        if redis_conn:
            return await redis_conn.get(key)  # type: ignore[misc]
        return None

    async def incr(self, key: str) -> int:
        if not self.redis:
            await self.connect()

        redis_conn = self.redis
        if redis_conn:
            return await redis_conn.incr(key)  # type: ignore[misc]
        return 0

    async def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        if not self.redis:
            await self.connect()

        redis_conn = self.redis
        if redis_conn:
            return await redis_conn.set(key, value, ex=ex)  # type: ignore[misc]
        return False

    async def expire(self, key: str, time: int) -> bool:
        if not self.redis:
            await self.connect()

        redis_conn = self.redis
        if redis_conn:
            return await redis_conn.expire(key, time)  # type: ignore[misc]
        return False

    async def delete(self, key: str) -> int:
        if not self.redis:
            await self.connect()

        redis_conn = self.redis
        if redis_conn:
            return await redis_conn.delete(key)  # type: ignore[misc]
        return 0

    async def xadd(self, stream: str, fields: dict) -> str:
        if not self.redis:
            await self.connect()

        redis_conn = self.redis
        if redis_conn:
            return await redis_conn.xadd(stream, fields)  # type: ignore[misc]
        return ""

    async def xgroup_create(self, stream: str, groupname: str, **kwargs) -> bool:
        if not self.redis:
            await self.connect()

        redis_conn = self.redis
        if redis_conn:
            await redis_conn.xgroup_create(stream, groupname, **kwargs)  # type: ignore[misc]
            return True
        return False

    async def xreadgroup(
        self, groupname: str, consumername: str, streams: dict, **kwargs
    ):
        if not self.redis:
            await self.connect()

        redis_conn = self.redis
        if redis_conn:
            return await redis_conn.xreadgroup(groupname, consumername, streams, **kwargs)  # type: ignore[misc]
        return []

    async def xack(self, stream: str, groupname: str, *ids) -> int:
        if not self.redis:
            await self.connect()

        redis_conn = self.redis
        if redis_conn:
            return await redis_conn.xack(stream, groupname, *ids)  # type: ignore[misc]
        return 0


# Global Instance
redis_client = RedisManager()  # Global Instance
