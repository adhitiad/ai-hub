from datetime import datetime, timezone
import asyncio
from src.core.logger import logger
from src.database.redis_client import redis_client
from src.database.database import db

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

                batch_docs = []
                batch_msg_ids = []

                for stream, messages in entries:
                    for message_id, data in messages:
                        # 3. PROSES BERAT DI SINI (Simpan DB / Trigger AI)
                        symbol = data[b"symbol"].decode("utf-8")
                        price = float(data[b"price"])

                        # Handle missing volume field gracefully just in case
                        volume_bytes = data.get(b"volume")
                        volume = float(volume_bytes) if volume_bytes else 0.0

                        batch_docs.append({
                            "symbol": symbol,
                            "price": price,
                            "volume": volume,
                            "timestamp": datetime.now(timezone.utc)
                        })
                        batch_msg_ids.append(message_id)

                if batch_docs:
                    # Simpan ke Mongo secara batch
                    await db.market_data.insert_many(batch_docs)

                    for doc in batch_docs:
                        logger.info("📥 Processed: %s at %s", doc["symbol"], doc["price"])

                    # 4. Acknowledge (Tandai sudah diproses) batch msg ids
                    await redis_client.xack(STREAM_KEY, GROUP_NAME, *batch_msg_ids)

            except Exception as e:
                logger.error("Stream Error: %s", e)
                await asyncio.sleep(1)

