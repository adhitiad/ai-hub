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
    data = await asyncio.to_thread(get_detailed_signal, symbol, asset_info)

    # Cek apakah sinyal berubah/baru (Logic sederhana)
    old_data = signal_bus.get_signal(symbol)
    is_new_signal = False

    if not old_data:
        if data["Action"] != "HOLD":
            is_new_signal = True
    elif old_data["Action"] != data["Action"] and data["Action"] != "HOLD":
        is_new_signal = True

    signal_bus.update_signal(symbol, data)

    # JIKA SINYAL BARU -> Broadcast ke User Premium/Enterprise
    if is_new_signal:
        formatted_msg = format_signal_message(data)

        # Ambil semua user yang punya telegram_chat_id & role premium/ent
        # (Anda perlu minta user input chat_id mereka di menu setting profil nanti)
        cursor = users_collection.find(
            {
                "telegram_chat_id": {"$exists": True},
                "role": {"$in": ["premium", "enterprise"]},
                "subscription_status": "active",
            }
        )

        async for user in cursor:
            send_telegram_message(user["telegram_chat_id"], formatted_msg)

    # --- 🛑 CEK JADWAL PASAR ---
    if not is_market_open(category):
        # Jika pasar tutup, kita skip prosesnya (Hemat resource & API Call)
        # Kita update status di RAM jadi 'Market Closed' biar keren di Dashboard
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

    try:
        # ... (Kode proses AI di bawah ini SAMA SEPERTI SEBELUMNYA) ...
        data = await asyncio.to_thread(get_detailed_signal, symbol, asset_info)

        if "error" in data:
            return False

        signal_bus.update_signal(symbol, data)

        if data["Action"] in ["BUY", "SELL"]:

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

                # Trigger Notif
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
            # Kita gunakan projection kosong {} untuk ambil semua field
            cursor = assets_collection.find({})
            assets = await cursor.to_list(length=2000)  # Support sampai 2000 aset

            if not assets:
                logger.warning(
                    "⚠️ No assets found in Database! Please run seed_assets.py"
                )
                await asyncio.sleep(60)
                continue

            # 2. Buat Task untuk setiap aset
            tasks = []
            for asset in assets:
                tasks.append(process_single(asset))

            # 3. Jalankan parallel
            await asyncio.gather(*tasks)

            signal_bus.save_snapshot()

            # Tunggu 60 detik sebelum scan ulang
            await asyncio.sleep(60)

        except Exception as e:
            logger.error(f"Producer Loop Error: {e}")
            await asyncio.sleep(10)
