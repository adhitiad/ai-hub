# src/core/signal_bus.py
from src.core.redis_client import redis_client


class InternalSignalBus:
    """
    Sekarang bertindak sebagai Proxy ke Redis.
    Tidak ada lagi variabel _storage lokal.
    """

    async def update_signal(self, symbol, data):
        # Fire and forget ke Redis
        await redis_client.set_signal(symbol, data)

    async def get_signal(self, symbol):
        return await redis_client.get_signal(symbol)

    async def get_all_signals(self):
        return await redis_client.get_all_signals()

    async def clear(self):
        """Clear all signals from Redis"""
        await redis_client.delete_pattern("signal:*")


# Instance
signal_bus = InternalSignalBus()
