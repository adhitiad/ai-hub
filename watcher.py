import asyncio
from datetime import datetime

import pandas as pd

# Setting agar yfinance lebih cepat (cache session)
import requests_cache
import yfinance as yf

from src.core.database import signals_collection
from src.core.logger import logger

session = requests_cache.CachedSession("yfinance.cache")
session.headers["User-agent"] = "my-program/1.0"


async def check_positions():
    """
    Looping mengecek semua sinyal 'OPEN' di Database MongoDB.
    Jika harga menyentuh SL/TP, status diupdate jadi WIN/LOSS.
    """
    logger.info("👀 Watcher Loop Started...")

    # 1. Ambil semua sinyal yang statusnya masih OPEN
    # Di MongoDB, kita pakai .find() dan to_list()
    cursor = signals_collection.find({"status": "OPEN"})
    active_signals = await cursor.to_list(length=1000)

    if not active_signals:
        # logger.info("No active signals to watch.")
        return

    print(f"Checking {len(active_signals)} active positions...")

    for sig in active_signals:
        symbol = sig["symbol"]

        try:
            # 2. Ambil Harga Real-time (1 Menit terakhir)
            # Kita download 1 hari data interval 1 menit untuk akurasi
            ticker = yf.Ticker(symbol, session=session)
            # Menggunakan 'fast_info' jika tersedia untuk last_price yang cepat,
            # atau history jika butuh OHLC
            # Disini kita pakai history 1m untuk cek High/Low barusan
            df = ticker.history(period="1d", interval="1m")

            if df.empty:
                continue

            # Ambil candle terakhir
            curr = df.iloc[-1]
            current_price = curr["Close"]
            high_price = curr["High"]
            low_price = curr["Low"]

            status = None
            pips = 0

            # 3. Logika Cek SL/TP
            # Prioritaskan SL (Stop Loss) -> Jika Low kena SL, berarti LOSS

            if sig["action"] == "BUY":
                # BUY: SL di bawah, TP di atas
                if low_price <= sig["sl"]:
                    status = "LOSS"
                    exit_price = sig["sl"]
                    pips = exit_price - sig["entry_price"]  # Pasti minus
                elif high_price >= sig["tp"]:
                    status = "WIN"
                    exit_price = sig["tp"]
                    pips = exit_price - sig["entry_price"]

            elif sig["action"] == "SELL":
                # SELL: SL di atas, TP di bawah
                if high_price >= sig["sl"]:
                    status = "LOSS"
                    exit_price = sig["sl"]
                    pips = sig["entry_price"] - exit_price  # Pasti minus
                elif low_price <= sig["tp"]:
                    status = "WIN"
                    exit_price = sig["tp"]
                    pips = sig["entry_price"] - exit_price

            # 4. Jika Status Berubah (Kena TP/SL), Update MongoDB
            if status:
                # Koreksi Pips untuk Forex (dikalikan scale) vs Saham
                # Kita anggap raw diff dulu, nanti bisa dikali scale dari config

                await signals_collection.update_one(
                    {"_id": sig["_id"]},
                    {
                        "$set": {
                            "status": status,
                            "exit_price": exit_price,
                            "pips": round(pips, 5),
                            "closed_at": datetime.utcnow(),
                        }
                    },
                )

                log_msg = (
                    f"🔔 POSITION CLOSED: {symbol} | {status} | PnL: {round(pips, 5)}"
                )
                if status == "WIN":
                    logger.info(f"💰 {log_msg}")
                else:
                    logger.warning(f"🔻 {log_msg}")

        except Exception as e:
            logger.error(f"Error checking {symbol}: {e}")


async def run_watcher():
    logger.info("🚀 AI TRADING WATCHER (MongoDB Version) STARTED")
    while True:
        await check_positions()
        # Cek setiap 30 detik agar tidak kena rate limit Yahoo Finance
        await asyncio.sleep(30)


if __name__ == "__main__":
    # Karena pakai Motor (Async MongoDB), kita harus jalankan loop asyncio
    try:
        asyncio.run(run_watcher())
    except KeyboardInterrupt:
        logger.info("Watcher stopped manually.")
