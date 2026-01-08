import asyncio
from datetime import datetime

from src.core.agent import get_detailed_signal

# Import database assets & signals
from src.core.database import assets_collection, signals_collection, users_collection
from src.core.logger import logger

# Import Logika Jadwal Baru
from src.core.market_schedule import is_market_open
from src.core.notifier import format_signal_message, send_telegram_message
from src.core.signal_bus import signal_bus
from src.core.telegram_notifier import telegram_bot


async def process_single(asset_info):
    symbol = asset_info["symbol"]
    category = asset_info.get("category", "UNKNOWN")

    # 1. Generate Signal
    # Ini adalah proses berat (AI/Data Fetching), kita tunggu hasilnya dulu
    data = await asyncio.to_thread(get_detailed_signal, symbol, asset_info)

    # --- PERBAIKAN: VALIDASI DATA ---
    # Jika data error atau tidak lengkap, hentikan proses untuk simbol ini
    if not data or "error" in data:
        # Uncomment baris bawah jika ingin melihat log error per aset (bisa spammy)
        logger.warning(f"⚠️ Skip {symbol}: {data.get('error', 'Unknown Error')}")
        return False

    if "Action" not in data:
        logger.warning(f"⚠️ Skip {symbol}: Invalid signal format (Missing 'Action')")
        return False
    # -------------------------------

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

        # Ambil user yang berhak menerima notifikasi
        cursor = users_collection.find(
            {
                "telegram_chat_id": {"$exists": True},
                "role": {"$in": ["premium", "enterprise"]},
                "subscription_status": "active",
            }
        )

        async for user in cursor:
            try:
                await send_telegram_message(user["telegram_chat_id"], formatted_msg)
            except Exception as e:
                logger.error(f"Failed to send telegram to {user.get('email')}: {e}")

    # 4. Cek Jadwal Pasar
    if not is_market_open(category):
        # Update status khusus jika pasar tutup
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
        # Kita gunakan data yang sudah diambil di awal (tidak perlu fetch ulang)

        if data["Action"] in ["BUY", "SELL"]:
            # Cek apakah sudah ada posisi OPEN yang sama
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

                # Trigger Notif Channel Telegram Umum (Bot Broadcast)
                if telegram_bot:
                    asyncio.create_task(telegram_bot.broadcast_signal(data))

        return True

    except Exception as e:
        logger.error(f"Worker Error {symbol}: {e}")
        return False


async def signal_producer_task():
    logger.info("🚀 PRODUCER STARTED (DB Mode)")
    while True:
        try:
            # 1. Ambil Semua Aset dari MongoDB
            cursor = assets_collection.find({})
            assets = await cursor.to_list(length=2000)

            if not assets:
                logger.warning("⚠️ No assets found in Database! Please run seed.py")
                await asyncio.sleep(60)
                continue

            # 2. Buat Task untuk setiap aset
            tasks = []
            for asset in assets:
                tasks.append(process_single(asset))

            # 3. Jalankan parallel (return_exceptions=True agar 1 error tidak mematikan semua)
            await asyncio.gather(*tasks, return_exceptions=True)

            # Simpan snapshot data signal bus ke disk/file (opsional)
            signal_bus.save_snapshot()

            # Tunggu 60 detik sebelum scan ulang
            await asyncio.sleep(60)

        except Exception as e:
            logger.error(f"Producer Loop Error: {e}")
            await asyncio.sleep(10)
