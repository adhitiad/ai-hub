import asyncio
import json

from src.core.database import db
from src.core.logger import logger
from src.core.redis_client import redis_client

STREAM_KEY = "market_ticks_stream"
GROUP_NAME = "backend_workers"
CONSUMER_NAME = "worker_1"


class StreamManager:
    async def publish_tick(self, symbol: str, price: float, volume: int):
        """
        Producer: Kirim data ke stream (sangat cepat, < 2ms)
        """
        data = {"symbol": symbol, "price": price, "volume": volume}
        # XADD key ID field string value string
        await redis_client.xadd(STREAM_KEY, data)

    async def start_consumer(self):
        """
        Consumer: Worker Background yang memproses data antrian
        """
        # 1. Buat Consumer Group (Hanya sekali)
        try:
            await redis_client.xgroup_create(STREAM_KEY, GROUP_NAME, mkstream=True)
        except:
            pass  # Group sudah ada

        print("🚀 Stream Consumer Started...")

        while True:
            try:
                # 2. Baca data dari stream
                entries = await redis_client.xreadgroup(
                    GROUP_NAME, CONSUMER_NAME, {STREAM_KEY: ">"}, count=10, block=2000
                )

                if not entries:
                    await asyncio.sleep(0.1)
                    continue

                for stream, messages in entries:
                    for message_id, data in messages:
                        # 3. PROSES BERAT DI SINI (Simpan DB / Trigger AI)
                        symbol = data[b"symbol"].decode("utf-8")
                        price = float(data[b"price"])

                        # Contoh: Simpan ke Mongo secara batch (simplified here)
                        # await db.market_data.insert_one({...})

                        logger.info(f"📥 Processed: {symbol} at {price}")

                        # 4. Acknowledge (Tandai sudah diproses)

                        await redis_client.xack(STREAM_KEY, GROUP_NAME, message_id)

            except Exception as e:
                logger.error(f"Stream Error: {e}")
                await asyncio.sleep(1)


# Cara Pakai di main.py:
# asyncio.create_task(StreamManager().start_consumer())# asyncio.create_task(StreamManager().start_consumer())
