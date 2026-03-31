import asyncio
import json
from datetime import datetime, timezone

from src.core.agent import get_detailed_signal
from src.core.logger import logger
from src.core.telegram_notifier import telegram_bot
from src.database.database import assets_collection, signals_collection
from src.database.redis_client import redis_client
from src.database.signal_bus import signal_bus
from src.feature.market_schedule import is_market_open
from src.feature.risk_manager import risk_manager

CONCURRENCY_LIMIT = 5


async def save_signal_background(signal_data):
    """Saves the trading signal data to the database."""
    try:
        await signals_collection.insert_one(signal_data)
        logger.info("💾 DB Async Save: %s", signal_data['symbol'])
    except Exception as e:
        logger.error("❌ DB Save Failed: %s", e)


async def process_single(asset_info):
    allowed, reason = await risk_manager.can_trade()

    if not allowed:
        logger.warning("⚠️ Daily Loss Limit Hit. Trading Paused. Reason: %s", reason)
        return False

    symbol = asset_info["symbol"]
    category = asset_info.get("category", "UNKNOWN")

    try:
        data = await get_detailed_signal(symbol, asset_info)
    except Exception as e:
        logger.error("⚠️ Error generating signal for %s: %s", symbol, e)
        return False

    if not data or (isinstance(data, dict) and "error" in data) or "Action" not in data:
        return False

    # 1. Cek Jadwal Pasar
    if not is_market_open(category):
        await signal_bus.update_signal(
            symbol,
            {
                "Symbol": symbol,
                "Action": "MARKET CLOSED",
                "Price": 0,
                "Prob": "0%",
                "AI_Analysis": "Market is currently closed.",
            },
        )
        return False

    # 2. Cek Perubahan Sinyal
    old_data = await signal_bus.get_signal(symbol)
    is_new_signal = False

    if not old_data:
        if data["Action"] != "HOLD":
            is_new_signal = True
    elif old_data.get("Action") != data["Action"] and data["Action"] != "HOLD":
        is_new_signal = True

    # 3. Selalu Update state terakhir di RAM (Signal Bus)
    await signal_bus.update_signal(symbol, data)

    # 4. Eksekusi jika benar-benar ada sinyal baru (BUY / SELL)
    if is_new_signal:
        action_upper = data["Action"].upper()
        if "BUY" in action_upper or "SELL" in action_upper:
            # Pastikan redis terkoneksi
            if not redis_client.redis:
                await redis_client.connect()
            redis_conn = redis_client.redis

            is_active = (
                await redis_conn.get(f"active_trade:{symbol}") if redis_conn else None
            )

            # Jika belum ada trade aktif untuk koin/saham ini
            if not is_active:
                logger.info("🚨 NEW SIGNAL DETECTED: %s - %s", symbol, data['Action'])

                # A. Broadcast ke Frontend (WebSocket via Redis Pub/Sub)
                if redis_conn:
                    try:
                        await redis_conn.publish("signal:all", json.dumps(data))
                        logger.info("🌐 Broadcasted %s to Frontend WS", symbol)
                    except Exception as e:
                        logger.error("Failed to publish to WS: %s", e)

                # B. Broadcast ke Telegram
                if telegram_bot:
                    asyncio.create_task(telegram_bot.broadcast_signal(data))

                # C. Simpan ke Database (Background)
                new_signal = {
                    "symbol": data["Symbol"],
                    "action": data["Action"],
                    "entry_price": data["Price"],
                    "tp": data["Tp"],
                    "sl": data["Sl"],
                    "lot_size": data.get("LotSize", 0),
                    "status": "OPEN",
                    "probability": data.get("ProbNum", 0),
                    "rank": data.get("Rank", "STANDARD"),
                    "asset_type": data.get("AssetType", "OFFSHORE"),
                    "created_at": datetime.now(timezone.utc),
                }
                asyncio.create_task(save_signal_background(new_signal))

                # D. Set Flag Anti-Spam di Redis (Expire 1 Jam)
                if redis_conn:
                    await redis_conn.setex(f"active_trade:{symbol}", 3600, "OPEN")

                return True

    return False


async def signal_producer_task():
    logger.info("🚀 PRODUCER STARTED (DB Mode & Safety Limit)")
    sem = asyncio.Semaphore(CONCURRENCY_LIMIT)

    async def bounded_process(asset):
        async with sem:
            await asyncio.sleep(0.1)
            return await process_single(asset)

    while True:
        try:
            cursor = assets_collection.find({})
            assets = await cursor.to_list(length=2000)

            if not assets:
                logger.warning("⚠️ No assets found in Database! Please run seed.py")
                await asyncio.sleep(60)
                continue

            tasks = [bounded_process(asset) for asset in assets]
            await asyncio.gather(*tasks, return_exceptions=True)

            await asyncio.sleep(60)

        except Exception as e:
            logger.error("Producer Loop Error: %s", e)
            await asyncio.sleep(10)
