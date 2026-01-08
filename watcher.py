import asyncio
from datetime import datetime

import pandas as pd
import pytz
import yfinance as yf

from src.core.database import alerts_collection, signals_collection
from src.core.logger import logger
from src.core.news_collector import analyze_news_sentiment, fetch_market_news

# HAPUS: import requests_cache


# HAPUS: session = requests_cache...


async def check_positions():
    """
    Looping mengecek semua sinyal 'OPEN' di Database MongoDB.
    Jika harga menyentuh SL/TP, status diupdate jadi WIN/LOSS.
    """
    logger.info("👀 Watcher Loop Started...")

    # 1. Ambil semua sinyal yang statusnya masih OPEN
    cursor = signals_collection.find({"status": "OPEN"})
    active_signals = await cursor.to_list(length=1000)

    if not active_signals:
        return

    print(f"Checking {len(active_signals)} active positions...")

    for sig in active_signals:
        symbol = sig["symbol"]

        try:
            # 2. Ambil Harga Real-time (1 Menit terakhir)
            ticker = yf.Ticker(symbol)

            # Ambil history 1 tahun, interval 1 jam
            df = ticker.history(period="1y", interval="1h")

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
            if sig["action"] == "BUY":
                if low_price <= sig["sl"]:
                    status = "LOSS"
                    exit_price = sig["sl"]
                    pips = exit_price - sig["entry_price"]
                elif high_price >= sig["tp"]:
                    status = "WIN"
                    exit_price = sig["tp"]
                    pips = exit_price - sig["entry_price"]

            elif sig["action"] == "SELL":
                if high_price >= sig["sl"]:
                    status = "LOSS"
                    exit_price = sig["sl"]
                    pips = sig["entry_price"] - exit_price
                elif low_price <= sig["tp"]:
                    status = "WIN"
                    exit_price = sig["tp"]
                    pips = sig["entry_price"] - exit_price

            # 4. Jika Status Berubah (Kena TP/SL), Update MongoDB
            if status:
                # Cek berita penyebab pergerakan
                news_items = fetch_market_news(symbol)
                sentiment_score, reason = analyze_news_sentiment(symbol, news_items)

                await signals_collection.update_one(
                    {"_id": sig["_id"]},
                    {
                        "$set": {
                            "status": status,
                            "exit_price": exit_price,
                            "pips": round(pips, 5),
                            "closed_at": datetime.now(),  # <--- PERBAIKAN DISINI (tambah kurung)
                            "news_context": {
                                "sentiment_score": sentiment_score,
                                "narrative": reason,
                                "headlines": [n["title"] for n in news_items],
                            },
                        }
                    },
                )

                log_msg = f"🔔 CLOSED {status}: {symbol} | PnL: {pips} | News: {reason} ({sentiment_score})"
                if status == "WIN":
                    logger.info(f"✅ {log_msg}")
                else:
                    logger.warning(f"❌ {log_msg}")

        except Exception as e:
            logger.error(f"Error checking {symbol}: {e}")
            pass


async def check_alerts(df, symbol):
    # 1. Ambil semua alert aktif untuk simbol ini
    cursor = alerts_collection.find({"symbol": symbol, "status": "ACTIVE"})
    alerts = await cursor.to_list(length=100)

    if not alerts or df.empty:
        return

    last_row = df.iloc[-1]
    current_price = last_row["Close"]

    for alert in alerts:
        triggered = False

        # Cek Price Alert
        if alert["type"] == "PRICE":
            if alert["condition"] == "ABOVE" and current_price >= alert["target_price"]:
                triggered = True
            elif (
                alert["condition"] == "BELOW" and current_price <= alert["target_price"]
            ):
                triggered = True

        # Cek Formula Alert
        elif alert["type"] == "FORMULA":
            safe_env = {
                "CLOSE": last_row["Close"],
                "RSI": last_row.get("RSI_14", 50),
                "VOLUME": last_row["Volume"],
                "SMA20": last_row.get("SMA_20", 0),
            }
            try:
                condition_str = alert["condition"].upper()
                for k, v in safe_env.items():
                    condition_str = condition_str.replace(k, str(v))

                if eval(condition_str):
                    triggered = True
            except:
                pass

        if triggered:
            logger.info(f"🚨 ALERT TRIGGERED: {symbol} - {alert['note']}")
            await alerts_collection.update_one(
                {"_id": alert["_id"]},
                {
                    "$set": {
                        "status": "TRIGGERED",
                        "triggered_at": datetime.utcnow(),  # Ini juga sebaiknya pakai ()
                    }
                },
            )


async def run_watcher():
    logger.info("🚀 AI TRADING WATCHER (MongoDB Version) STARTED")
    while True:
        await check_positions()
        # Cek setiap 30 detik
        await asyncio.sleep(30)


if __name__ == "__main__":
    try:
        asyncio.run(run_watcher())
    except KeyboardInterrupt:
        logger.info("Watcher stopped manually.")
