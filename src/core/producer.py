import asyncio
from datetime import datetime

from src.core.agent import get_detailed_signal
from src.core.database import assets_collection, signals_collection, users_collection
from src.core.logger import logger
from src.core.market_schedule import is_market_open
from src.core.notifier import format_signal_message, send_telegram_message
from src.core.risk_manager import (
    risk_manager,
)  # Pastikan ada instance global risk_manager
from src.core.signal_bus import signal_bus
from src.core.telegram_notifier import telegram_bot

# --- KONFIGURASI SAFETY ---
# Batasi hanya 5-10 request bersamaan agar tidak kena Rate Limit / Banned IP
CONCURRENCY_LIMIT = 5


async def process_single(asset_info):
    """Proses sinyal untuk satu aset secara async"""
    # PERBAIKAN: Tambahkan 'await' dan unpack return value
    allowed, reason = await risk_manager.can_trade()

    if not allowed:
        # Kita bisa pakai variable 'reason' agar log lebih jelas
        logger.warning(f"⚠️ Daily Loss Limit Hit. Trading Paused. Reason: {reason}")
        return False
    symbol = asset_info["symbol"]
    category = asset_info.get("category", "UNKNOWN")

    try:
        # Panggil langsung dengan await (jangan pakai to_thread untuk fungsi async)
        data = await get_detailed_signal(symbol, asset_info)

    except Exception as e:
        logger.error(f"⚠️ Error generating signal for {symbol}: {e}")
        return False

    # --- Validasi Data ---
    if not data or isinstance(data, dict) and "error" in data:
        return False

    if "Action" not in data:
        return False

    # 2. Cek apakah sinyal berubah (Logic Update Signal Bus)
    old_data = signal_bus.get_signal(symbol)
    is_new_signal = False

    if not old_data:
        if data["Action"] != "HOLD":
            is_new_signal = True
    elif old_data.get("Action") != data["Action"] and data["Action"] != "HOLD":
        is_new_signal = True

    # Update state terakhir di RAM (Signal Bus)
    signal_bus.update_signal(symbol, data)

    # 3. Broadcast ke User Premium jika ada sinyal baru
    if is_new_signal:
        formatted_msg = format_signal_message(data)

        cursor = users_collection.find(
            {
                "telegram_chat_id": {"$exists": True},
                "role": {"$in": ["premium", "enterprise"]},
                "subscription_status": "active",
            }
        )

        async for user in cursor:
            try:
                # Fire and forget
                asyncio.create_task(
                    send_telegram_message(user["telegram_chat_id"], formatted_msg)
                )
            except Exception as e:
                logger.error(f"Failed to send telegram to {user.get('email')}: {e}")

    # 4. Cek Jadwal Pasar
    if not is_market_open(category):
        signal_bus.update_signal(
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

    # 5. Eksekusi Auto-Trading (Masuk Database Signals)
    try:
        action_upper = data["Action"].upper()
        if "BUY" in action_upper or "SELL" in action_upper:
            existing_position = await signals_collection.find_one(
                {"symbol": symbol, "status": "OPEN"}
            )

            if not existing_position:
                new_signal = {
                    "symbol": data["Symbol"],
                    "action": data["Action"],
                    "entry_price": data["Price"],
                    "tp": data["Tp"],
                    "sl": data["Sl"],
                    "lot_size": data["LotSize"],
                    "status": "OPEN",
                    "created_at": datetime.utcnow(),
                }

                await signals_collection.insert_one(new_signal)
                logger.info(f"💾 SAVED DB: {symbol} {data['Action']}")

                # Trigger Notif Channel Telegram Umum
                if telegram_bot:
                    asyncio.create_task(telegram_bot.broadcast_signal(data))

        return True

    except Exception as e:
        logger.error(f"Worker DB Save Error {symbol}: {e}")
        return False


async def signal_producer_task():
    logger.info("🚀 PRODUCER STARTED (DB Mode & Safety Limit)")

    # Semaphore untuk "mengantre" task agar tidak membom server
    sem = asyncio.Semaphore(CONCURRENCY_LIMIT)

    async def bounded_process(asset):
        """Wrapper agar worker harus antre tiket (Semaphore) dulu sebelum jalan"""
        async with sem:
            # Sedikit delay random agar pola request tidak terbaca sebagai bot agresif
            await asyncio.sleep(0.1)
            return await process_single(asset)

    while True:
        try:
            # 1. Ambil Semua Aset
            cursor = assets_collection.find({})
            assets = await cursor.to_list(length=2000)

            if not assets:
                logger.warning("⚠️ No assets found in Database! Please run seed.py")
                await asyncio.sleep(60)
                continue

            # 2. Buat Task dengan Rate Limiter
            # Kita map setiap aset ke fungsi bounded_process
            tasks = [bounded_process(asset) for asset in assets]

            logger.info(
                f"🔄 Scanning {len(assets)} assets (Concurrency: {CONCURRENCY_LIMIT})..."
            )

            # 3. Jalankan parallel (tapi dibatasi semaphore di dalamnya)
            await asyncio.gather(*tasks, return_exceptions=True)

            # Simpan snapshot
            signal_bus.save_snapshot()

            logger.info("✅ Scan cycle finished. Sleeping...")
            # Tunggu 60 detik sebelum scan ulang
            await asyncio.sleep(60)

        except Exception as e:
            logger.error(f"Producer Loop Error: {e}")
            await asyncio.sleep(10)
